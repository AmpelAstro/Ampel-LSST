#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/ingest/LSSTPhotoCombiner.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 20.04.2021
# Last Modified Date: 20.04.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from typing import Tuple, Set, Union
from ampel.type import DataPointId, ChannelId
from ampel.content.DataPoint import DataPoint
from ampel.ingest.T1PhotoCombiner import T1PhotoCombiner
from ampel.content.Compound import CompoundElement


class LSSTPhotoCombiner(T1PhotoCombiner):

	require = "channel",

	def __init__(self, **kwargs):

		super().__init__(**kwargs)

		if not self.resource:
			raise ValueError("Resource missing")

		if not self.resource.get('channel'):
			raise ValueError("Resource 'channels' is missing")

		self.chan_config = self.resource.get('channel')

	def gen_sub_entry(self, # type: ignore[override]
		dp: DataPoint, channel_name: ChannelId
	) -> Tuple[Union[DataPointId, CompoundElement], Set[str]]:

		tags = {"LSST"}
		opts = self.chan_config[channel_name]

		comp_entry: DataPointId = {'id': dp['_id']}

		# POLICIES
		#  Photopoint option: check if updated zero point should be used
		if 'useUpdatedZP' in opts['policy'] and "HAS_UPDATED_ZP" in dp['tag']:
			comp_entry['tag'] = [1]
			tags.add("HAS_CUSTOM_POLICY")

		# EXCLUSIONS
		# Check access permission (public / partners)
		if "LSST_PUB" in dp['tag']:
			tags.add("LSST_PUB")
			if "LSST_PUB" not in opts['access']:
				dp['excl'] = "Private"
				tags.add("HAS_DATARIGHT_EXCLUSION")

		elif "excl" in dp.get("excl", []): # type: ignore
			comp_entry['excl'] = "Manual"
			tags.add("HAS_EXCLUDED_PPS")
			tags.add("MANUAL_EXCLUSION")

		#  Check for superseded
		elif "SUPERSEDED" in dp['tag']:
			comp_entry['excl'] = "Superseded"
			tags.add("HAS_EXCLUDED_PPS")
			tags.add("SUPERSEDED_PPS")

		return comp_entry, tags
