#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/ingest/LSSTPhotoPointShaper.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 20.04.2021
# Last Modified Date: 20.04.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from typing import Dict, List, Any, Iterable, Optional
from ampel.abstract.AbsT0Unit import AbsT0Unit
from ampel.content.DataPoint import DataPoint
from ampel.protocol.LoggerProtocol import LoggerProtocol


class LSSTPhotoPointShaper(AbsT0Unit):
	"""
	This class 'shapes' datapoints in a format suitable
	to be saved into the ampel database
	"""

	# override
	logger: Optional[LoggerProtocol] # type: ignore[assignment]

	# Mandatory implementation
	def ampelize(self, arg: Iterable[Dict[str, Any]]) -> List[DataPoint]:
		"""
		:param arg: sequence of unshaped pps
		IMPORTANT:
		1) This method *modifies* the input dicts (it removes 'candid' and programpi),
		even if the unshaped pps are ReadOnlyDict instances
		2) 'stock' is not set here on purpose since it would then conflicts with the $addToSet operation
		"""

		# ret_list: List[DataPoint] = []
		raise NotImplementedError()
		# return ret_list
