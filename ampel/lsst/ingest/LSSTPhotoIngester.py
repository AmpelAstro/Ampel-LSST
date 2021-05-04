#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/ingest/LSSTPhotoIngester.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 20.04.2021
# Last Modified Date: 20.04.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

import itertools
from pymongo import UpdateOne
from typing import Dict, List, Any
from ampel.type import StockId
from ampel.util.mappings import unflatten_dict
from ampel.lsst.ingest.LSSTPhotoPointShaper import LSSTPhotoPointShaper
from ampel.content.DataPoint import DataPoint
from ampel.alert.AmpelAlert import AmpelAlert
from ampel.abstract.AbsT0Unit import AbsT0Unit
from ampel.abstract.ingest.AbsAlertContentIngester import AbsAlertContentIngester


class LSSTPhotoIngester(AbsAlertContentIngester[AmpelAlert, DataPoint]):

	check_reprocessing: bool = True

	# Set default for alert_history_length
	alert_history_length: int = 30

	pp_shaper: AbsT0Unit = LSSTPhotoPointShaper()

	# Standard projection used when checking DB for existing PPS
	projection: Dict[str, int] = {
		'_id': 1, 'tag': 1, 'excl': 1,
		'body.jd': 1, 'body.filterName': 1,
	}

	def __init__(self, **kwargs) -> None:
		super().__init__(**kwargs)

		self._photo_col = self.context.db.get_collection("t0")
		self.stat_pps_inserts = 0
		self._projection_spec = unflatten_dict(self.projection)

	def project(self, doc: DataPoint) -> DataPoint:
		return self._project(doc, self._projection_spec)


	def _project(self, doc, projection):
		out: Dict[str, Any] = {}
		for key, spec in projection.items():
			if key not in doc:
				continue

			if isinstance(spec, dict):
				item = doc[key]
				if isinstance(item, list):
					out[key] = [self._project(v, spec) for v in item]
				elif isinstance(item, dict):
					out[key] = self._project(item, spec)
			else:
				out[key] = doc[key]
		return out

	def _try_ingest(self, stock_id: StockId, dps: List[DataPoint]) -> List[DataPoint]:
		"""
		Attempt to insert ingest pps into the t0 collection, marking
		superseded points.
		"""

		# Part 1: gather info from DB and alert
		#######################################

		# New pps lists for db loaded datapoints
		dps_db: List[DataPoint] = list(self._photo_col.find({'stock': stock_id}, self.projection))

		ops = []
		if self.check_reprocessing:
			add_update = lambda op: ops.append(op)
		else:
			add_update = self.updates_buffer.add_t0_update

		# Create set with pp ids from alert
		ids_dps_alert = {el['_id'] for el in dps}

		# python set of ids of photopoints from DB
		ids_dps_db = {el['_id'] for el in dps_db}

		# uniquify photopoints by jd, rcid. for duplicate points, choose the
		# one with the larger _id
		ids_dps_superseded = dict()
		unique_dps = dict()
		for dp in sorted(itertools.chain(dps, dps_db), key=lambda dp: dp['_id']):
			key = dp['body']['jd']

			if key not in unique_dps:
				unique_dps[key] = dp['_id']
			elif dp['_id'] > unique_dps[key]:
				ids_dps_superseded[unique_dps[key]] = dp['_id']
				unique_dps[key] = dp['_id']
			elif dp['_id'] < unique_dps[key]:
				ids_dps_superseded[dp['_id']] = unique_dps[key]

		# Part 2: Insert new data points
		################################

		# Difference between candids from the alert and candids present in DB
		ids_dps_to_insert = ids_dps_alert - ids_dps_db

		for dp in dps:
			if dp['_id'] in ids_dps_to_insert:
				base = {k: v for k, v in dp.items() if k not in {'tag', 'stock'}}
				sets: Dict[str, Any] = {
					'stock': stock_id,
					'tag': {'$each': dp['tag']}
				}
				# If alerts were received out of order, this point may already
				# be superseded.
				if (
					self.check_reprocessing and
					dp['_id'] in ids_dps_superseded and
					'SUPERSEDED' not in dp['tag']
				):
					# NB: here we modify the point in place, so the SUPERSEDED
					# tag remains in place if there is a second pass
					dp['tag'] = list(dp['tag']) + ['SUPERSEDED']
					sets['tag']['$each'] = dp['tag']
					sets['newId'] = ids_dps_superseded[dp['_id']]
					self.logd['logs'].append(
						f'Marking datapoint {dp["_id"]} '
						f'as superseded by {ids_dps_superseded[dp["_id"]]}'
					)
					self.stat_pps_reprocs += 1
				# Unconditionally update the doc
				add_update(
					UpdateOne(
						{'_id': dp['_id']},
						{
							'$setOnInsert': base,
							'$addToSet': sets
						},
						upsert=True
					)
				)
				self.stat_pps_inserts += 1

		# Part 3: Update data points that were superseded
		#################################################

		for dp in (dps_db if self.check_reprocessing else []):
			if (
				dp['_id'] in ids_dps_superseded and
				'SUPERSEDED' not in dp['tag']
			):
				dp['tag'] = list(dp['tag']) + ['SUPERSEDED']
				sets = {
					'tag': {'$each': dp['tag']},
					'newId': ids_dps_superseded[dp['_id']]
				}
				add_update(
					UpdateOne(
						{'_id': dp['_id']},
						{
							'$addToSet': sets
						},
						upsert=False
					)
				)
				self.stat_pps_reprocs += 1

		# If no photopoint exists in the DB, then this is a new transient.
		if not ids_dps_db:
			self.logd['extra']['new'] = True

		# Part 4: commit ops and check for conflicts
		############################################
		if self.check_reprocessing:
			# Commit ops, retrying on upsert races
			if ops:
				self.updates_buffer.call_bulk_write('t0', ops)
			# If another query returns docs not present in the first query, the
			# set of superseded photopoints may be incomplete.
			if concurrent_updates := (
				{
					doc['_id']
					for doc in self._photo_col.find({'stock': stock_id}, {'_id': 1})
				} \
				- (ids_dps_db | ids_dps_alert)
			):
				raise ConcurrentUpdateError(f"t0 collection contains {len(concurrent_updates)} extra photopoints: {concurrent_updates}")

		# Photo data that will be part of the compound. Points are projected
		# the same way whether they were drawn from the db or from the alert.
		datapoints = [
			el for el in (
				dps_db + [
					self.project(dp)
					for dp in dps if dp['_id'] in ids_dps_to_insert
				]
			)
			# Only return datapoints that were in the alert itself
			# https://github.com/AmpelProject/Ampel-ZTF/issues/6
			if el['_id'] in ids_dps_alert
		]

		return sorted(datapoints, key=lambda k: k['body']['jd'])


	# Mandatory implementation
	def ingest(self, alert: AmpelAlert) -> List[DataPoint]:
		# Attention: ampelize *modifies* dict instances loaded by fastavro
		dps = self.pp_shaper.ampelize(alert.dps)
		return self._try_ingest(alert.stock_id, dps)


	# Mandatory implementation
	def get_stats(self, reset: bool = True) -> Dict[str, Any]:

		ret = {
			'pps': self.stat_pps_inserts,
		}

		if reset:
			self.stat_pps_inserts = 0

		return ret
