#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-ZTF/ampel/ztf/t2/T2LightCurveFeatures.py
# License           : BSD-3-Clause
# Author            : Jakob van Santen <jakob.van.santen@desy.de>
# Date              : 15.04.2021
# Last Modified Date: 15.04.2021
# Last Modified By  : Jakob van Santen <jakob.van.santen@desy.de>

from typing import Any, Dict, Optional

import numpy as np
import light_curve

from ampel.abstract.AbsLightCurveT2Unit import AbsLightCurveT2Unit
from ampel.abstract.AbsTabulatedT2Unit import AbsTabulatedT2Unit
from ampel.types import UBson
from ampel.view.LightCurve import LightCurve


class T2LightCurveFeatures(AbsLightCurveT2Unit, AbsTabulatedT2Unit):
    """
    Calculate various features of the light curve using the light-curve
    package described in https://ui.adsabs.harvard.edu/abs/2021MNRAS.502.5147M%2F/abstract
    """

    #: Features to extract from the light curve.
    #: See: https://docs.rs/light-curve-feature/0.2.2/light_curve_feature/features/index.html
    features: Dict[str, Optional[Dict[str, Any]]] = {
        "InterPercentileRange": {"quantile": 0.25},
        "LinearFit": None,
        "StetsonK": None,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.extractor = light_curve.Extractor(
            *(getattr(light_curve, k)(**(v or {})) for k, v in self.features.items())
        )

    def process(self, lightcurve: LightCurve) -> UBson:
        fluxtable = self.get_flux_table(lightcurve)
        result = {}
        for band in set(fluxtable['band']):
            mask = fluxtable['band'] == band
            t = np.asarray(fluxtable[mask]['time'])
            flux = np.asarray(fluxtable[mask]['flux'])
            fluxerr = np.asarray(fluxtable[mask]['fluxerr'])

            try:
                result.update(
                    {
                        f"{k}_{band}": v
                        for k, v in zip(
                            self.extractor.names, self.extractor(t, flux, fluxerr)
                        )
                    }
                )
            except ValueError:
                # raised if too few points
                ...
        return result
