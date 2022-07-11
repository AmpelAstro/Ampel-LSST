#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/alert/LSSTAlertSupplier.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 20.04.2021
# Last Modified Date: 21.03.2022
# Last Modified By  : Marcus Fenner <mf@physik.hu-berlin.de>

from typing import Literal, Optional

from ampel.alert.AmpelAlert import AmpelAlert
from ampel.alert.BaseAlertSupplier import BaseAlertSupplier
from ampel.protocol.AmpelAlertProtocol import AmpelAlertProtocol
from ampel.view.ReadOnlyDict import ReadOnlyDict


class DIAObjectMissingError(Exception):
    """
    Raised when there is no DIAObject in the alert
    """

    ...


class LSSTAlertSupplier(BaseAlertSupplier):
    """
    Iterable class that, for each alert payload provided by the underlying alert_loader,
    returns an AmpelAlert instance.
    """

    # Override default
    deserialize: Optional[Literal["avro", "json"]] = "avro"

    @staticmethod
    def _shape(d: dict) -> AmpelAlertProtocol:
        if d["diaObject"]:
            diaObjectId = d["diaObject"]["diaObjectId"]
            dps = [ReadOnlyDict(d["diaSource"])]
            if d.get("prvDiaSources"):
                for prv_source in d["prvDiaSources"]:
                    dps.append(ReadOnlyDict(prv_source))
            if d.get("prvDiaForcedSources"):
                for forced_source in d["prvDiaForcedSources"]:
                    dps.append(ReadOnlyDict(forced_source))
            if d.get("diaNondetectionLimit"):
                for non_det in d["diaNondetectionLimit"]:
                    dps.append(ReadOnlyDict(non_det))
            if d.get("diaObject"):
                dps.append(ReadOnlyDict(d["diaObject"]))
            return AmpelAlert(
                id=d["alertId"],  # alert id
                stock=diaObjectId,  # internal ampel id
                datapoints=tuple(dps),
                extra={"kafka": kafka} if (kafka := d.get("__kafka")) else None,
            )
        else:
            raise DIAObjectMissingError

    def __next__(self) -> AmpelAlertProtocol:
        """
        :returns: a dict with a structure that AlertConsumer understands
        :raises StopIteration: when alert_loader dries out.
        :raises AttributeError: if alert_loader was not set properly before this method is called
        """
        d = self._deserialize(next(self.alert_loader))

        return self._shape(d)

        
