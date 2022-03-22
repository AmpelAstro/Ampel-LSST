#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/aux/LSSTobjFilter.py
# License           : BSD-3-Clause
# Author            : Marcus Fenner <mf@physik.hu-berlin.de>
# Date              : 22.03.2022
# Last Modified Date: 22.03.2022
# Last Modified By  : Marcus Fenner <mf@physik.hu-berlin.de>

from typing import List

from ampel.content.DataPoint import DataPoint

from ampel.abstract.AbsApplicable import AbsApplicable


class LSSTObjFilter(AbsApplicable):
    """
    Get diaObject for metadata
    """

    def apply(self, arg: List[DataPoint]) -> List[DataPoint]:
        return [el for el in arg if "LSST_OBJ" in el["tag"]]
