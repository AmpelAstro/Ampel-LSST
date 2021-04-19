#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/ingest/LSSTUpperLimitShaper.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 20.04.2021
# Last Modified Date: 20.04.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from typing import Dict, List, Any, Iterable, Optional
from ampel.abstract.AbsT0Unit import AbsT0Unit
from ampel.content.DataPoint import DataPoint
from ampel.protocol.LoggerProtocol import LoggerProtocol


class LSSTUpperLimitShaper(AbsT0Unit):
	"""
	This class 'shapes' upper limits in a format suitable
	to be saved into the ampel database
	"""

	# override
	logger: Optional[LoggerProtocol] # type: ignore[assignment]

	# Mandatory implementation
	def ampelize(self, arg: Iterable[Dict[str, Any]]) -> List[DataPoint]:
		"""
		'stock' (prev. called tranId) is not set here on purpose
		since it would then conflicts with the $addToSet operation
		"""

		raise NotImplementedError()
