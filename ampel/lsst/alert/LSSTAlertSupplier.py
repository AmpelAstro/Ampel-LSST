#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/alert/LSSTAlertSupplier.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 20.04.2021
# Last Modified Date: 14.09.2021
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

    def __next__(self) -> AmpelAlertProtocol:
        """
        :returns: a dict with a structure that AlertConsumer understands
        :raises StopIteration: when alert_loader dries out.
        :raises AttributeError: if alert_loader was not set properly before this method is called
        """
        d = self._deserialize(next(self.alert_loader))  # type: ignore

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
            return AmpelAlert(
                id=d["alertId"],  # alert id
                stock=diaObjectId,  # internal ampel id
                datapoints=tuple(dps),
            )
        else:
            raise DIAObjectMissingError
