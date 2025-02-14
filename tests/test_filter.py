from pathlib import Path

import fastavro
import numpy as np
import pytest

from ampel.log.AmpelLogger import AmpelLogger
from ampel.lsst.alert.LSSTAlertSupplier import LSSTAlertSupplier
from ampel.lsst.t0.ReallySimpleLSSTFilter import ReallySimpleLSSTFilter


@pytest.fixture
def alerts():
    with open(
        Path(__file__).parent / "test-data" / "schema_701.avro", "rb"
    ) as f:
        return [LSSTAlertSupplier._shape(a) for a in fastavro.reader(f)]


@pytest.fixture
def ampel_logger():
    return AmpelLogger.get_logger()


def test_filter(alerts, ampel_logger):
    filt = ReallySimpleLSSTFilter(
        logger=ampel_logger, min_ndet=0, min_tspan=0, max_tspan=np.inf
    )
    for alert in alerts:
        assert filt.process(alert) is True
