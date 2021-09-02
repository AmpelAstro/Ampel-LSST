#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/ingest/LSSTDataPointShaper.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 20.04.2021
# Last Modified Date: 25.08.2021
# Last Modified By  : mf <mf@physik.hu-berlin.de>

from typing import Dict, List, Any, Iterable, Optional
from ampel.types import StockId
from ampel.abstract.AbsT0Unit import AbsT0Unit
from ampel.content.DataPoint import DataPoint
from ampel.protocol.LoggerProtocol import LoggerProtocol

class LSSTDataPointShaper(AbsT0Unit):
	"""
	This class 'shapes' datapoints in a format suitable
	to be saved into the ampel database
	"""

	# override
	logger: Optional[LoggerProtocol] # type: ignore[assignment]

	# Mandatory implementation
	def process(self, arg: Iterable[Dict[str, Any]], stock: StockId) -> List[DataPoint]:
		"""
		:param arg: sequence of unshaped dps
		"""

		ret_list: List[DataPoint] = []
		setitem = dict.__setitem__
		popitem = dict.pop

		for photo_dict in arg:
			if 'diaSourceId' in photo_dict:
				id = photo_dict['diaSourceId']
			elif 'diaForcedSourceId' in photo_dict:
				id = photo_dict['diaForcedSourceId']
			else:
				raise NotImplementedError
			ret_list.append(
				{
					'id': id,
					'stock': stock,
					'tag': ['LSST','LSST_' + photo_dict['filterName'].upper()],
					'body': photo_dict
				}
			)
		return ret_list
