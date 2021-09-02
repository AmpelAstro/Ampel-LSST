#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/ingest/LSSTStockIngester.py
# License           : BSD-3-Clause
# Author            : mf <mf@physik.hu-berlin.de>
# Date              : 04.05.2021
# Last Modified Date: 04.05.2021
# Last Modified By  : mf <mf@physik.hu-berlin.de>

from ampel.ingest.StockIngester import StockIngester
from typing import Dict, List, Any, Union
from ampel.type import StockId

class LSSTStockIngester(StockIngester):

	# Override
	tag: List[Union[int, str]] = ["LSST"]

	# Override
	def get_setOnInsert(self, stock_id: StockId) -> Dict[str, Any]:
		return {
			'tag': self.tag,
		}
