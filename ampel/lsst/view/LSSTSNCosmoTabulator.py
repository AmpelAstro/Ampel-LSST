#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/view/LSSTSNCosmoTabulator.py
# License           : BSD-3-Clause
# Author            : mf <mf@physik.hu-berlin.de>
# Date              : 25.05.2021
# Last Modified Date: 31.08.2021
# Last Modified By  : mf <mf@physik.hu-berlin.de>

from typing import Sequence, Dict, Optional, List, Any, Tuple, Union, Callable, Literal, Iterable, TypedDict
from ampel.content.DataPoint import DataPoint
from ampel.abstract.AbsSNCosmoTabulator import AbsSNCosmoTabulator
from astropy.table import Table
from ampel.view.LightCurve import LightCurve
from ampel.content.T1Document import T1Document

LSST_BANDPASSES = {
    'u': "lsstu",
    'g': "lsstg",
    'r': "lsstr",
    'i': "lssti",
    'z': "lsstz",
    'y': "lssty",
}
class LSSTSNCosmoTabulator(AbsSNCosmoTabulator):
    """ """
    def get_photo_table(self, compound: T1Document, dps: Union[LightCurve, List[DataPoint]]) -> Table:
        if isinstance(dps, LightCurve):
            flux,fluxerr,filtername,midPointTai = dps.get_ntuples(('psFlux','psFluxErr','filterName','midPointTai'))
            filters = [ LSST_BANDPASSES[filter] for filter in filtername ]
        else:
            flux = [ el['body']['psFlux'] for el in dps if 'LSST' in el['tag']]
            fluxerr = [ el['body']['psFluxErr'] for el in dps if 'LSST' in el['tag']]
            filters = [ LSST_BANDPASSES[el['body']['filterName']] for el in dps if 'LSST' in el['tag']]
            midPointTai = [ el['body']['midPointTai'] for el in dps if 'LSST' in el['tag']]
        return Table(
            {
                "time": midPointTai,
                "flux": flux,
                "fluxerr": fluxerr,
                "band": filters,
                "zp": [25] * len(filters),
                "zpsys": ["ab"] * len(filters),
            },
            dtype = ('float64', 'float64', 'float64', 'str', 'int64', 'str' )
        )

    def get_pos(self, compound: T1Document, dps: Union[LightCurve, List[DataPoint]]) -> Sequence[Tuple[Any, Any]]:
        if isinstance(dps, LightCurve):
            return dps.get_tuples('ra','decl')
        return [(el['body']['ra'],el['body']['decl']) for el in dps if ('LSST' in el['tag'] and 'ra' in el['body'])]

    def get_jd(self, compound: T1Document, dps: Union[LightCurve, List[DataPoint]]) -> Sequence[Any]:
        if isinstance(dps, LightCurve):
            return [ time - 2400000.5 for time in dps.get_value('midPointTai')]
        return [ el['body']['midPointTai'] - 2400000.5 for el in dps if 'LSST' in el['tag']]
