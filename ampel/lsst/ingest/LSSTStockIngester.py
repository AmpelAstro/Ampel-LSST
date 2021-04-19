#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/ingest/LSSTStockIngester.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 20.04.2021
# Last Modified Date: 20.04.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from typing import Dict, List, Any, Union
from ampel.type import StockId
from ampel.lsst.util.LSSTIdMapper import to_lsst_id
from ampel.mongo.update.StockIngester import StockIngester


class LSSTStockIngester(StockIngester):

	# Override
	tag: List[Union[int, str]] = ["LSST"]

	# Override
	def get_setOnInsert(self, stock_id: StockId) -> Dict[str, Any]:
		return {
			'tag': self.tag,
			'name': [to_lsst_id(stock_id)] # type: ignore[arg-type]
		}
