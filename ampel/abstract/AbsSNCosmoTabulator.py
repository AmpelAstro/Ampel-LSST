#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-lsst/ampel/abstract/AbsSNCosmoTabulator.py
# License           : BSD-3-Clause
# Author            : mf <mf@physik.hu-berlin.de>
# Date              : 25.05.2021
# Last Modified Date: 31.08.2021
# Last Modified By  : mf <mf@physik.hu-berlin.de>

from typing import Sequence, Dict, Optional, List, Any, Tuple, Union, Callable, Literal, Iterable
from ampel.base.AmpelBaseModel import AmpelBaseModel
from ampel.base.AmpelABC import AmpelABC
from ampel.content.DataPoint import DataPoint
from astropy.table import Table
from ampel.view.LightCurve import LightCurve
from ampel.base.decorator import abstractmethod
from ampel.content.T1Document import T1Document

class AbsSNCosmoTabulator(AmpelABC, AmpelBaseModel, abstract=True):
    """ """
    @abstractmethod
    def get_photo_table(self, compound: T1Document, dps: Union[LightCurve, List[DataPoint]]) -> Table:
        ...

    @abstractmethod
    def get_pos(self, compound: T1Document, dps: Union[LightCurve, List[DataPoint]]) -> Sequence[Tuple[Any, Any]]:
        ...

    @abstractmethod
    def get_jd(self, compound: T1Document, dps: Union[LightCurve, List[DataPoint]]) -> Sequence[Any]:
        ...
