#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/aux/LSSTFPFilter.py
# License           : BSD-3-Clause
# Author            : Marcus Fenner <mf@physik.hu-berlin.de>
# Date              : 15.09.2021
# Last Modified Date: 15.09.2021
# Last Modified By  : Marcus Fenner <mf@physik.hu-berlin.de>

from typing import List

from ampel.content.DataPoint import DataPoint

from ampel.abstract.AbsApplicable import AbsApplicable


class LSSTFPFilter(AbsApplicable):
    """
    Only get LSST's forced photometry datapoints
    """

    def apply(self, arg: List[DataPoint]) -> List[DataPoint]:
        return [el for el in arg if "LSST_FP" in el["tag"]]
