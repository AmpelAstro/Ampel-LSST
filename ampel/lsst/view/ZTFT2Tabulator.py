#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/view/ZTFT2Tabulator.py
# License           : BSD-3-Clause
# Author            : mf <mf@physik.hu-berlin.de>
# Date              : 26.05.2021
# Last Modified Date: 13.09.2021
# Last Modified By  : mf <mf@physik.hu-berlin.de>

from typing import Sequence, Optional, List, Any, Tuple, Union
from ampel.content.DataPoint import DataPoint
from ampel.abstract.AbsT2Tabulator import AbsT2Tabulator
from astropy.table import Table
from ampel.view.LightCurve import LightCurve
import numpy as np
from ampel.content.T1Document import T1Document

ZTF_BANDPASSES = {
    1: {"name": "ztfg"},
    2: {"name": "ztfr"},
    3: {"name": "ztfi"},
}

class ZTFT2Tabulator(AbsT2Tabulator):


    def get_flux_table(self, dps: Union[LightCurve, List[DataPoint]], compound: Optional[T1Document] = None) -> Table:

        light_curve = self.to_lightcurve(dps, compound)
        if ( values := light_curve.get_ntuples(('magpsf','sigmapsf','jd','fid')) ) is None:
            magpsf, sigmapsf, jd, fids = ([],[],[],[])
        else:
            magpsf, sigmapsf, jd, fids = zip(*values)
        filter_names = [ZTF_BANDPASSES[fid]['name'] for fid in fids]
        flux = np.asarray([ 10 ** (-((mgpsf) - 25)/2.5) for mgpsf in magpsf])
        fluxerr = np.abs(flux * (-np.asarray(sigmapsf) / 2.5 * np.log(10)))
        return Table(
            {
                "time": jd,
                "flux": flux,
                "fluxerr": fluxerr,
                "band": filter_names,
                "zp": [25] * len(filter_names),
                "zpsys": ["ab"] * len(filter_names),
            },
            dtype = ('float64', 'float64', 'float64', 'str', 'int64', 'str' )
        )

    def get_pos(self, dps: Union[LightCurve, List[DataPoint]], compound: Optional[T1Document] = None) -> Sequence[Tuple[Any, Any]]:
        return self.to_lightcurve(dps, compound).get_pos('raw')

    def get_jd(self, dps: Union[LightCurve, List[DataPoint]], compound: Optional[T1Document] = None) -> Sequence[Any]:
        if result := self.to_lightcurve(dps, compound).get_values('jd'):
            return result
        else:
            return []

    @staticmethod
    def to_lightcurve(dps: Union[LightCurve, List[DataPoint]], compound: Optional[T1Document] = None) -> LightCurve:
        if isinstance(dps, LightCurve):
            return dps
        else:
            assert compound is not None
            return LightCurve.build(compound=compound, datapoints=[dp for dp in dps if 'ZTF' in dp['tag']])
