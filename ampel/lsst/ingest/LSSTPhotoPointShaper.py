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
from astropy.time import Time

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
		1) This method *modifies* the input dicts (it changes some keys to ZTF keys),
		even if the unshaped pps are ReadOnlyDict instances
		2) 'stock' is not set here on purpose since it would then conflicts with the $addToSet operation
		"""

		ret_list: List[DataPoint] = []
		setitem = dict.__setitem__
		popitem = dict.pop

		keymap = {
			'decl': 'dec',
			'x': 'xpos',
			'y': 'ypos',
		}
		# Map FilterName to FID to be ZTF compatible
		# Keep in mind that wavelenghts differ!
		filter = {
			'u': 0,
			'g': 1,
			'r': 2,
			'i': 3,
			'z': 4,
			'y': 5
		}

		for photo_dict in arg:
			for oldkey, newkey in keymap.items():
				if oldkey in photo_dict:
					setitem(photo_dict, newkey, popitem(photo_dict, oldkey))
			time = Time(photo_dict['midPointTai'], format="mjd", scale='tai')
			time.format = 'jd' # Todo: check timescale
			setitem(photo_dict, 'fid', filter[photo_dict['filterName']])
			setitem(photo_dict, 'jd', time.value)

			ret_list.append(
				{
					'_id': photo_dict['diaObjectId'],
					'tag': ['LSST','LSST_' + photo_dict['filterName']],
					'body': photo_dict
				}
			)

		return ret_list
