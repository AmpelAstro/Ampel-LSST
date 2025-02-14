#!/usr/bin/env python
# File              : Ampel-LSST/ampel/lsst/alert/LSSTAlertSupplier.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 20.04.2021
# Last Modified Date: 21.03.2022
# Last Modified By  : Marcus Fenner <mf@physik.hu-berlin.de>

from collections.abc import Iterator
from itertools import chain
from typing import Literal

from ampel.alert.AmpelAlert import AmpelAlert
from ampel.alert.BaseAlertSupplier import BaseAlertSupplier
from ampel.protocol.AmpelAlertProtocol import AmpelAlertProtocol
from ampel.view.ReadOnlyDict import ReadOnlyDict


class DIAObjectMissingError(Exception):
    """
    Raised when there is no DIAObject in the alert
    """

    ...


# Translate 2022-era field names to schema 7.x
_field_upgrades: dict[str, str] = {
    "midPointTai": "midpointMjdTai",
    "psFlux": "psfFlux",
    "psFluxErr": "psfFluxErr",
    "filterName": "band",
    "decl": "dec",
}


class LSSTAlertSupplier(BaseAlertSupplier):
    """
    Iterable class that, for each alert payload provided by the underlying alert_loader,
    returns an AmpelAlert instance.
    """

    # Override default
    deserialize: None | Literal["avro", "json"] = "avro"

    @staticmethod
    def _shape_dp(d: dict) -> ReadOnlyDict:
        return ReadOnlyDict(
            {_field_upgrades.get(k, k): v for k, v in d.items()}
        )

    @classmethod
    def _shape(cls, d: dict) -> AmpelAlertProtocol:
        if d["diaObject"]:
            diaObjectId = d["diaObject"]["diaObjectId"]
            dps = tuple(
                cls._shape_dp(dp)
                for dp in chain(
                    (d["diaSource"],),
                    d.get("prvDiaSources") or (),
                    d.get("prvDiaForcedSources") or (),
                    d.get("diaNondetectionLimit") or (),
                    ((d.get("diaObject"),) if d.get("diaObject") else ()),
                )
            )
            return AmpelAlert(
                id=d["alertId"],  # alert id
                stock=diaObjectId,  # internal ampel id
                datapoints=tuple(dps),
                extra={"kafka": kafka}
                if (kafka := d.get("__kafka"))
                else None,
            )
        raise DIAObjectMissingError

    def acknowledge(self, alerts: Iterator[AmpelAlertProtocol]) -> None:
        # invert transformation applied in _shape()
        self.alert_loader.acknowledge(
            {"__kafka": alert.extra["kafka"]}  # type: ignore[misc]
            for alert in alerts
            if alert.extra and "kafka" in alert.extra
        )

    def __next__(self) -> AmpelAlertProtocol:
        """
        :returns: a dict with a structure that AlertConsumer understands
        :raises StopIteration: when alert_loader dries out.
        :raises AttributeError: if alert_loader was not set properly before this method is called
        """
        d = self._deserialize(next(self.alert_loader))

        return self._shape(d)
