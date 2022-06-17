#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-LSST/ampel/lsst/alert/ElasticcAlertSupplier.py
# License           : BSD-3-Clause
# Author            : j nordin <jnordin@physik.hu-berlin.de>
# Date              : 9.6.2022
# Last Modified Date: 9.6.2022
# Last Modified By  : j nordin <jnordin@physik.hu-berlin.de>

import sys
from typing import Literal, Optional
from hashlib import blake2b
from bson import encode

from ampel.alert.AmpelAlert import AmpelAlert
from ampel.alert.BaseAlertSupplier import BaseAlertSupplier
from ampel.protocol.AmpelAlertProtocol import AmpelAlertProtocol
from ampel.view.ReadOnlyDict import ReadOnlyDict




class ElasticcAlertSupplier(BaseAlertSupplier):
    """
    Iterable class that, for each lightcurve provided by the underlying alert_loader,
    returns an AmpelAlert instance.
    """

    # Override default
    deserialize: Optional[Literal["avro", "json"]]

    def __next__(self) -> AmpelAlertProtocol:
        """
        :returns: a dict with a structure that AlertConsumer understands
        :raises StopIteration: when alert_loader dries out.
        :raises AttributeError: if alert_loader was not set properly before this method is called
        """

        lc = self._deserialize(next(self.alert_loader))

        # Are these actually unique?
        stock = int( lc.meta['snid'] )
        sntype = lc.meta['sim_type_index']   # Again do not know how consistent these are

        # Generate datapoints.
        # Would be much more efficient if dps generation was done in Loader?
        dps = []
        all_ids = b""
        df = lc.to_pandas()
        for k, row in df.iterrows():
            d = dict(row)
            # Generate point id through hash
            d_hash = blake2b(encode(d), digest_size=7).digest()
            # We will call this a diaSourceId if it is associated with a detection
            # Only these are asigned and obsvered magn
            if d['cause_alert']:
                d['diaSourceId'] = int.from_bytes(d_hash, byteorder=sys.byteorder)
            else:
                # Take this to be forced photometry
                d['diaForcedSourceId'] = int.from_bytes(d_hash, byteorder=sys.byteorder)
            all_ids += d_hash
            dps.append( ReadOnlyDict(d) )


        # Create alert id through hash of obs dates
        alert_id=int.from_bytes( # alert id
            blake2b(all_ids, digest_size=7).digest(),
            byteorder=sys.byteorder
        )

        # Add meta as content of diaObject + alert info
        d = dict(lc.meta)
        d['alertId'] = alert_id
        # Is it an issue that diaObjectId is the same as stock?
        d['diaObjectId'] = stock
        dps.append(ReadOnlyDict(d))




        return AmpelAlert(
            id=alert_id,  # alert id
            stock=stock,  # internal ampel id
            datapoints=tuple(dps),
            tag = ['GENTYPE'+str(sntype)]
        )