#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/ingest/LSSTPhotoIngester.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 20.04.2021
# Last Modified Date: 20.04.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from typing import Dict, List, Any
from ampel.lsst.ingest.LSSTPhotoPointShaper import LSSTPhotoPointShaper
from ampel.lsst.ingest.LSSTUpperLimitShaper import LSSTUpperLimitShaper
from ampel.content.DataPoint import DataPoint
from ampel.alert.PhotoAlert import PhotoAlert
from ampel.abstract.ingest.AbsAlertContentIngester import AbsAlertContentIngester


class LSSTPhotoIngester(AbsAlertContentIngester[PhotoAlert, DataPoint]):


	def __init__(self, **kwargs) -> None:
		super().__init__(**kwargs)
		self.pp_shaper = LSSTPhotoPointShaper()
		self.ul_shaper = LSSTUpperLimitShaper()
		self.stat_pps_inserts = 0
		self.stat_uls_inserts = 0


	# Mandatory implementation
	def ingest(self, alert: PhotoAlert) -> List[DataPoint]:
		# Attention: ampelize *modifies* dict instances loaded by fastavro
		dps = self.pp_shaper.ampelize(alert.pps) + (self.ul_shaper.ampelize(alert.uls) if alert.uls else [])
		raise NotImplementedError()


	# Mandatory implementation
	def get_stats(self, reset: bool = True) -> Dict[str, Any]:

		ret = {
			'pps': self.stat_pps_inserts,
			'uls': self.stat_uls_inserts
		}

		if reset:
			self.stat_pps_inserts = 0
			self.stat_uls_inserts = 0

		return ret
