#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-LSST/ampel/lsst/t2/T2GetAlertJournal.py
# License:             BSD-3-Clause
# Author:              Marcus Fennner <mf@physik.hu-berlinn.de>
# Date:                31.03.2022
# Last Modified Date:  31.03.2022
# Last Modified By:    Marcus Fennner <mf@physik.hu-berlinn.de>

from typing import ClassVar, List, Union
from ampel.types import UBson
from ampel.abstract.AbsStockT2Unit import AbsStockT2Unit
from ampel.content.StockDocument import StockDocument
from ampel.struct.UnitResult import UnitResult
from ampel.model.DPSelection import DPSelection


class T2GetAlertJournal(AbsStockT2Unit):
    """
    Get the alert journal of an LSST stock
    """

    def process(self, stock_doc: StockDocument) -> Union[UBson, UnitResult]:
        return [
            journal for journal in stock_doc["journal"] if journal["tier"] == 0
        ]
