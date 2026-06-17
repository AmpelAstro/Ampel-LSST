from collections import Counter
from pathlib import Path

import bson
import numpy as np
import pytest

from ampel.lsst.view.LSSTT2Tabulator import LSSTT2Tabulator


@pytest.fixture
def datapoints():
    return bson.decode(
        (Path(__file__).parent / "test-data" / "25409136044802058.bson").read_bytes()
    )["datapoints"]


def test_tabulator(datapoints):
    tags = {"LSST_FP": {}, "LSST_DP": {}}
    for dp in datapoints:
        for k, v in tags.items():
            if k in dp["tag"]:
                v[dp["body"]["midpointMjdTai"]] = dp["body"]["psfFlux"]
    dp_if_not_fp = [
        tags["LSST_FP"].get(t, tags["LSST_DP"].get(t, np.nan))
        for t in sorted(tags["LSST_DP"] | tags["LSST_FP"])
    ]
    tab = LSSTT2Tabulator(zp=31.5).get_flux_table(datapoints)
    assert len(tab) < len(datapoints)
    assert len(np.unique(tab["time"])) == len(tab["time"])
    assert tab["flux"][np.argsort(tab["time"])].tolist() == dp_if_not_fp

    # source column is assigned
    source_counts = Counter(tab["source"])
    assert source_counts["LSST_FP"] == 4
    assert source_counts["LSST_DP"] == len(tab) - 4
    # id column is assigned and unique
    assert len(np.unique(tab["id"])) == len(tab)
