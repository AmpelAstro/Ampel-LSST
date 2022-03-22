#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/view/ZTFT2Tabulator.py
# License           : BSD-3-Clause
# Author            : Marcus Fenner <mf@physik.hu-berlin.de>
# Date              : 26.05.2021
# Last Modified Date: 21.03.2022
# Last Modified By  : Marcus Fenner <mf@physik.hu-berlin.de>

from typing import Any, List, Sequence, Tuple

import numpy as np
from ampel.content.DataPoint import DataPoint
from astropy.table import Table

from ampel.abstract.AbsT2Tabulator import AbsT2Tabulator
from ampel.ztf.util.ZTFIdMapper import ZTFIdMapper

ZTF_BANDPASSES = {
    1: {"name": "ztfg"},
    2: {"name": "ztfr"},
    3: {"name": "ztfi"},
}

signdict = {
    "0": -1,
    "f": -1,
    "1": 1,
    "t": 1,
}


class ZTFT2Tabulator(AbsT2Tabulator):
    def get_flux_table(
        self,
        dps: List[DataPoint],
    ) -> Table:
        magpsf, sigmapsf, jd, fids, magzpsci, isdiffpos = self.get_values(
            dps, ["magpsf", "sigmapsf", "jd", "fid", "magzpsci", "isdiffpos"]
        )
        filter_names = [ZTF_BANDPASSES[fid]["name"] for fid in fids]
        signs = [signdict[el] for el in isdiffpos]
        flux = signs * np.asarray(
            [10 ** (-((mgpsf) - 25) / 2.5) for mgpsf in magpsf]
        )
        fluxerr = np.abs(flux * (-np.asarray(sigmapsf) / 2.5 * np.log(10)))
        return Table(
            {
                "time": jd,
                "flux": flux,
                "fluxerr": fluxerr,
                "band": filter_names,
                "zp": magzpsci,
                "zpsys": ["ab"] * len(filter_names),
            },
            dtype=("float64", "float64", "float64", "str", "int64", "str"),
        )

    def get_pos(self, dps: List[DataPoint]) -> Sequence[Tuple[float, float]]:
        return tuple(zip(*self.get_values(dps, ["ra", "dec"])))

    def get_jd(
        self,
        dps: List[DataPoint],
    ) -> Sequence[Any]:
        return self.get_values(dps, "jd")[0]

    def get_stock_id(self, dps: List[DataPoint]) -> set[int]:  # type: ignore[override]
        return set([stock for el in dps if "ZTF" in el["tag"] for stock in el["stock"]])  # type: ignore[misc]

    def get_stock_name(self, dps: List[DataPoint]) -> list[str]:  # type: ignore[override]
        return [ZTFIdMapper.to_ext_id(el) for el in self.get_stock_id(dps)]

    @staticmethod
    def get_values(
        dps: List[DataPoint], params: Sequence[str]
    ) -> Tuple[Sequence[Any], ...]:
        if tup := tuple(
            map(
                list,
                zip(
                    *(
                        [el["body"][param] for param in params]
                        for el in dps
                        if "ZTF" in el["tag"]
                    )
                ),
            )
        ):
            return tup
        else:
            return tuple([[]] * len(params))
