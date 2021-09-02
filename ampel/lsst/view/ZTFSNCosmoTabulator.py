#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/view/ZTFSNCosmoTabulator.py
# License           : BSD-3-Clause
# Author            : mf <mf@physik.hu-berlin.de>
# Date              : 26.05.2021
# Last Modified Date: 02.09.2021
# Last Modified By  : mf <mf@physik.hu-berlin.de>

from typing import Sequence, Dict, Optional, List, Any, Tuple, Union, Callable, Literal, Iterable
from ampel.content.DataPoint import DataPoint
from ampel.abstract.AbsSNCosmoTabulator import AbsSNCosmoTabulator
from astropy.table import Table
from ampel.view.LightCurve import LightCurve
from time import time
import numpy as np
from ampel.content.T1Document import T1Document

ZTF_BANDPASSES = {
    1: {"name": "ztfg"},
    2: {"name": "ztfr"},
    3: {"name": "ztfi"},
}

class ZTFSNCosmoTabulator(AbsSNCosmoTabulator):


    def get_photo_table(self, compound: T1Document, dps: Union[LightCurve, List[DataPoint]]) -> Table:

        light_curve = self.to_lightcurve(compound, dps)
        if ( values := light_curve.get_ntuples(('magpsf','sigmapsf','jd','fid')) ) is None:
            magpsf, sigmapsf, jd, fids = ([],[],[],[])
        else:
            magpsf, sigmapsf, jd, fids = zip(*values)
        filter_names = [ZTF_BANDPASSES[fid]['name'] for fid in fids]
        flux = np.asarray([ 10 ** (-((mgpsf) - 25)/2.5) for mgpsf in magpsf])
        sigmapsf = np.asarray(sigmapsf)
        fluxerr = np.abs(flux * (-sigmapsf / 2.5 * np.log(10)))
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

    def get_pos(self, compound: T1Document, dps: Union[LightCurve, List[DataPoint]]) -> Sequence[Tuple[Any, Any]]:
        return self.to_lightcurve(compound, dps).get_pos('raw')

    def get_jd(self, compound: T1Document, dps: Union[LightCurve, List[DataPoint]]) -> Sequence[Any]:
        return self.to_lightcurve(compound, dps).get_values('jd')

    def to_lightcurve(self, compound: T1Document, dps: Union[LightCurve, List[DataPoint]]) -> LightCurve:
        if isinstance(dps, LightCurve):
            return dps
        else:
            return LightCurve.build(compound=compound, datapoints=[dp for dp in dps if 'ZTF' in dp['tag']])
