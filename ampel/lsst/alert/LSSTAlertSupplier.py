#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/alert/LSSTAlertSupplier.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 20.04.2021
# Last Modified Date: 20.04.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from typing import Literal, List, Union, Callable, Any, Dict
from ampel.lsst.util.LSSTIdMapper import to_ampel_id
from ampel.alert.PhotoAlert import PhotoAlert
from ampel.abstract.AbsAlertSupplier import AbsAlertSupplier


class LSSTAlertSupplier(AbsAlertSupplier[PhotoAlert]):
	"""
	Iterable class that, for each alert payload provided by the underlying alert_loader,
	returns an PhotoAlert instance.
	"""

	# Override default
	deserialize: Union[None, Literal["avro", "json"], Callable[[Any], Dict]] = "avro"


	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.stat_pps = 0
		self.stat_uls = 0


	def __next__(self) -> PhotoAlert:
		"""
		:returns: a dict with a structure that AlertProcessor understands
		:raises StopIteration: when alert_loader dries out.
		:raises AttributeError: if alert_loader was not set properly before this method is called
		"""
		d = self.deserialize(
			next(self.alert_loader) # type: ignore
		)

		# Return PhotoAlert
		raise NotImplementedError()


	def get_stats(self, reset: bool = True) -> Dict[str, Any]:

		ret = {'pps': self.stat_pps, 'uls': self.stat_uls}
		if reset:
			self.stat_pps = 0
			self.stat_uls = 0
		return ret
