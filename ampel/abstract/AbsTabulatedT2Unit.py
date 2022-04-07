#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-lsst/ampel/abstract/AbsTabulatedT2Unit.py
# License           : BSD-3-Clause
# Author            : Marcus Fenner <mf@physik.hu-berlin.de>
# Date              : 08.08.2021
# Last Modified Date: 17.03.2022
# Last Modified By  : Marcus Fenner <mf@physik.hu-berlin.de>

from typing import Any, ClassVar, Dict, List, Optional, Sequence, Union

from ampel.base.AmpelABC import AmpelABC
from ampel.base.AuxUnitRegister import AuxUnitRegister
from ampel.base.LogicalUnit import LogicalUnit
from ampel.content.DataPoint import DataPoint
from ampel.model.UnitModel import UnitModel
from astropy.table import Table, vstack

from ampel.abstract.AbsT2Tabulator import AbsT2Tabulator
import math


class AbsTabulatedT2Unit(AmpelABC, LogicalUnit, abstract=True):
    """
    Base class for T2s that operate on tabulated data.
    """

    ingest: ClassVar[Dict[str, Any]]
    tabulator: Sequence[UnitModel] = []

    def __init__(self, **kwargs) -> None:
        self.tabulator = kwargs["tabulator"]
        super().__init__(**kwargs)
        self._tab_engines: Sequence[AbsT2Tabulator] = [
            AuxUnitRegister.new_unit(model=el, sub_type=AbsT2Tabulator)
            for el in self.tabulator
        ]

    def get_flux_table(
        self,
        dps: List[DataPoint],
        jd_start: Optional[float] = None,
        jd_end: Optional[float] = None,
    ) -> Table:
        tables = [tab.get_flux_table(dps) for tab in self._tab_engines]
        if len(tables) == 1:
            table = tables[0]
        elif len(tables) > 1:
            table = vstack(tables, join_type="exact")
        else:
            raise NotImplementedError
        table.sort("time")
        if jd_start and not math.isinf(jd_start):
            mask = table["time"] < jd_start
            table = table[~mask]
        if jd_end and not math.isinf(jd_end):
            mask = table["time"] < jd_end
            table = table[~mask]
        return table

    def get_stock_id(
        self,
        dps: List[DataPoint],
    ) -> List[int]:
        return [
            stock
            for tab in self._tab_engines
            for stock in tab.get_stock_id(dps)
        ]

    def get_stock_name(
        self,
        dps: List[DataPoint],
    ) -> List[Union[str, int]]:
        return [
            name
            for tab in self._tab_engines
            for name in tab.get_stock_name(dps)
        ]