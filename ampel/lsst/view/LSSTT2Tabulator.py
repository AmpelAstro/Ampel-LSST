#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/view/LSSTT2Tabulator.py
# License           : BSD-3-Clause
# Author            : Marcus Fenner <mf@physik.hu-berlin.de>
# Date              : 25.05.2021
# Last Modified Date: 05.05.2022
# Last Modified By  : Marcus Fenner <mf@physik.hu-berlin.de>

from typing import Any, Sequence, Iterable

from ampel.content.DataPoint import DataPoint
from ampel.types import StockId
from astropy.table import Table

from ampel.abstract.AbsT2Tabulator import AbsT2Tabulator

LSST_BANDPASSES = {
    "u": "lsstu",
    "g": "lsstg",
    "r": "lsstr",
    "i": "lssti",
    "z": "lsstz",
    "y": "lssty",
}


class LSSTT2Tabulator(AbsT2Tabulator):
    convert2jd: bool = True
    zp: float
    """ """

    def get_flux_table(
        self,
        dps: Iterable[DataPoint],
    ) -> Table:
        flux, fluxerr, filtername, tai = self.get_values(
            dps, ["psFlux", "psFluxErr", "filterName", "midPointTai"]
        )
        if self.convert2jd:
            tai = self._to_jd(tai)
        filters = list(map(LSST_BANDPASSES.get, filtername))

        return Table(
            {
                "time": tai,
                "flux": flux,
                "fluxerr": fluxerr,
                "band": filters,
                # ZP for ELAsTiCC, might need to be corrected for LSST!
                "zp": [self.zp] * len(filters),
                "zpsys": ["ab"] * len(filters),
            },
            dtype=("float64", "float64", "float64", "str", "float64", "str"),
        )

    def get_positions(
        self, dps: Iterable[DataPoint]
    ) -> Sequence[tuple[float, float, float]]:
        return tuple(
            zip(self.get_jd(dps), *self.get_values(dps, ["ra", "decl"]))
        )

    def get_jd(self, dps: Iterable[DataPoint]) -> Sequence[float]:
        return self._to_jd(self.get_values(dps, ["midPointTai"])[0])

    @staticmethod
    def _to_jd(dates: Sequence[Any]) -> Sequence[Any]:
        return [date + 2400000.5 for date in dates]

    def get_stock_id(self, dps: Iterable[DataPoint]) -> set[StockId]:
        return set(
            sum(
                [
                    list(stockid)
                    if isinstance(stockid := el["stock"], Sequence) and not isinstance(stockid, (str, bytes))
                    else [stockid]
                    for el in dps
                    if "LSST" in el["tag"]
                ],
                [],
            )
        )

    def get_stock_name(self, dps: Iterable[DataPoint]) -> list[str]:
        return [str(stock) for stock in self.get_stock_id(dps)]

    @staticmethod
    def get_values(
        dps: Iterable[DataPoint], params: Sequence[str]
    ) -> tuple[Sequence[Any], ...]:
        if tup := tuple(
            map(
                list,
                zip(
                    *(
                        [el["body"][param] for param in params]
                        for el in dps
                        if ("LSST_DP" in el["tag"] or "LSST_FP" in el["tag"])
                    )
                ),
            )
        ):
            return tup
        else:
            return tuple([[]] * len(params))
