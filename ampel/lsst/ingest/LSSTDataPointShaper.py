#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/ingest/LSSTDataPointShaper.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 20.04.2021
# Last Modified Date: 13.09.2021
# Last Modified By  : Marcus Fenner <mf@physik.hu-berlin.de>

from typing import Any, Dict, Iterable, List
from bson import encode

from ampel.content.DataPoint import DataPoint
from ampel.types import StockId
from ampel.util.hash import hash_payload

from ampel.abstract.AbsT0Unit import AbsT0Unit


class LSSTDataPointShaper(AbsT0Unit):
    """
    This class 'shapes' datapoints in a format suitable
    to be saved into the ampel database
    """

    digest_size: int = 8  # Byte width of datapoint ids
    # Mandatory implementation

    def process(
        self, arg: Iterable[Dict[str, Any]], stock: StockId
    ) -> List[DataPoint]:
        """
        :param arg: sequence of unshaped dps
        """

        ret_list: List[DataPoint] = []
        setitem = dict.__setitem__

        for photo_dict in arg:
            tags = ["LSST", "LSST_" + photo_dict["filterName"].upper()]
            setitem(photo_dict, "filterName", photo_dict["filterName"].lower())
            if "diaSourceId" in photo_dict:
                id = photo_dict["diaSourceId"]
                tags.append("LSST_DP")
            elif "diaForcedSourceId" in photo_dict:
                id = photo_dict["diaForcedSourceId"]
                tags.append("LSST_FP")
            else:
                # Nondetection Limit
                id = hash_payload(
                    encode(dict(sorted(photo_dict.items()))),
                    size=-self.digest_size * 8,
                )
                tags.append("LSST_ND")
            ret_list.append(
                {"id": id, "stock": stock, "tag": tags, "body": photo_dict}
            )
        return ret_list
