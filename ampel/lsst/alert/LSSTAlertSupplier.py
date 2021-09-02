#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/alert/LSSTAlertSupplier.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 20.04.2021
# Last Modified Date: 01.09.2021
# Last Modified By  : mf <mf@physik.hu-berlin.de>

from typing import Literal, List, Union, Callable, Any, Dict
from ampel.alert.AmpelAlert import AmpelAlert
from ampel.alert.BaseAlertSupplier import BaseAlertSupplier
from ampel.view.ReadOnlyDict import ReadOnlyDict

class DIAObjectMissingError(Exception):
	"""
	Raised when there is no DIAObject in the alert
	"""
	...

class LSSTAlertSupplier(BaseAlertSupplier[AmpelAlert]):
	"""
	Iterable class that, for each alert payload provided by the underlying alert_loader,
	returns an AmpelAlert instance.
	"""

	# Override default
	deserialize: Union[None, Literal["avro", "json"], Callable[[Any], Dict]] = "avro"

	def __next__(self) -> AmpelAlert:
		"""
		:returns: a dict with a structure that AlertConsumer understands
		:raises StopIteration: when alert_loader dries out.
		:raises AttributeError: if alert_loader was not set properly before this method is called
		"""
		d = self.deserialize(
			next(self.alert_loader) # type: ignore
		)

		if d['diaObject']:
			diaObjectId = d['diaObject']['diaObjectId']
			dps = [ReadOnlyDict(d['diaSource'])]
			if d['prvDiaSources']:
				for prv_source in d['prvDiaSources']:
					dps.append(ReadOnlyDict(prv_source))
			if d['prvDiaForcedSources']:
				for forced_source in d['prvDiaForcedSources']:
					dps.append(ReadOnlyDict(forced_source))
			return AmpelAlert(
				id = d['alertId'], # alert id
				stock_id = diaObjectId, # internal ampel id
				dps = tuple(dps),
			)
		else:
			raise DIAObjectMissingError
