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
