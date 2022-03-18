#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/ingest/LSSTMongoMuxer.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 14.12.2017
# Last Modified Date: 18.03.2022
# Last Modified By  : Marcus Fenner <mf@physik.hu-berlin.de>

from typing import Any, Dict, List, Optional, Tuple

from ampel.content.DataPoint import DataPoint
from ampel.mongo.utils import maybe_use_each
from ampel.types import StockId
from ampel.util.mappings import unflatten_dict
from pymongo import UpdateOne

from ampel.abstract.AbsT0Muxer import AbsT0Muxer


class LSSTMongoMuxer(AbsT0Muxer):
    """
    This class compares info between alert and DB so that only the needed info is ingested later.

    :param alert_history_length: alerts must not contain all available info for a given transient.
    Alerts for LSST should provide a photometric history of 365 days.
    """

    alert_history_length: int = 365

    # Standard projection used when checking DB for existing PPS/ULS
    projection = {
        "_id": 0,
        "id": 1,
        "tag": 1,
        "channel": 1,
        "excl": 1,
        "stock": 1,
        "body.midPointTai": 1,
        "body.filterName": 1,
        "body.psFlux": 1,
    }

    def __init__(self, **kwargs) -> None:

        super().__init__(**kwargs)

        # used to check potentially already inserted pps
        self._photo_col = self.context.db.get_collection("t0")
        self._projection_spec = unflatten_dict(self.projection)

    def process(
        self, dps_al: List[DataPoint], stock_id: Optional[StockId] = None
    ) -> Tuple[Optional[List[DataPoint]], Optional[List[DataPoint]]]:
        """
        :param dps_al: datapoints from alert
        :param stock_id: stock id from alert
        Attempt to determine which pps/uls should be inserted into the t0 collection,
        and which one should be marked as superseded.
        """

        # Part 1: gather info from DB and alert
        #######################################

        # New pps/uls lists for db loaded datapoints
        dps_db: List[DataPoint] = list(
            self._photo_col.find({"stock": stock_id}, self.projection)
        )

        add_update = self.updates_buffer.add_t0_update

        # Create set with datapoint ids from alert
        ids_dps_alert = {el["id"] for el in dps_al}

        # python set of ids of datapoints from DB
        ids_dps_db = {el["id"] for el in dps_db}

        # Part 2: Insert new data points
        ################################

        # Difference between candids from the alert and candids present in DB
        ids_dps_to_insert = ids_dps_alert - ids_dps_db

        for dp in dps_al:

            if dp["id"] in ids_dps_to_insert:

                add_to_set = {"stock": stock_id}
                add_to_set["tag"] = maybe_use_each(dp["tag"])

                # Unconditionally update the doc
                add_update(
                    UpdateOne(
                        {"id": dp["id"]},
                        {
                            "$setOnInsert": {
                                k: v
                                for k, v in dp.items()
                                if k not in {"tag", "stock"}
                            },
                            "$addToSet": add_to_set,
                        },
                        upsert=True,
                    )
                )

        dps_combine = dps_al

        return [
            dp for dp in dps_al if dp["id"] in ids_dps_to_insert
        ], dps_combine

    def _project(self, doc, projection):

        out: Dict[str, Any] = {}
        for key, spec in projection.items():

            if key not in doc:
                continue

            if isinstance(spec, dict):
                item = doc[key]
                if isinstance(item, list):
                    out[key] = [self._project(v, spec) for v in item]
                elif isinstance(item, dict):
                    out[key] = self._project(item, spec)
            else:
                out[key] = doc[key]

        return out
