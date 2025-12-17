import pytest
import requests

from ampel.content.DataPoint import DataPoint
from ampel.content.StockDocument import StockDocument
from ampel.core.AmpelContext import AmpelContext
from ampel.log.AmpelLogger import AmpelLogger
from ampel.lsst.t3.complement.LSSTCutoutImages import LSSTCutoutImages
from ampel.model.UnitModel import UnitModel
from ampel.struct.AmpelBuffer import AmpelBuffer
from ampel.struct.T3Store import T3Store


@pytest.fixture(scope="session")
def _archive_service_reachable():
    base_url = LSSTCutoutImages.validate({})["archive_url"]
    try:
        requests.head(base_url, timeout=0.5, verify=False)
    except requests.exceptions.Timeout:
        pytest.skip("LSST archive is unreachable")


@pytest.mark.usefixtures("_archive_service_reachable")
def test_lsstcutoutimages(
    mock_context: AmpelContext, ampel_logger: AmpelLogger
) -> None:
    unit = mock_context.loader.new_context_unit(
        model=UnitModel(unit="LSSTCutoutImages", config={"insecure": True}),
        logger=ampel_logger,
        context=mock_context,
        sub_type=LSSTCutoutImages,
    )
    buf = AmpelBuffer(
        {
            "id": 0,
            "stock": StockDocument(
                {
                    "stock": 0,
                    "tag": [],
                    "channel": [],
                    "journal": [],
                    "ts": {},
                    "updated": 0,
                    "name": ["sourceysource"],
                }
            ),
            "t0": [
                DataPoint(
                    {
                        "id": 169738308673863748,
                        "tag": ["LSST_DP"],
                        "body": {"midpointMjdTai": 60000.0, "psfFlux": 1500.0},
                    }
                ),
                DataPoint(
                    {
                        "id": 169676640861290517,
                        "tag": ["LSST_DP"],
                        "body": {"midpointMjdTai": 60001.0, "psfFlux": 1400.0},
                    }
                ),
            ],
        }
    )
    unit.complement([buf], T3Store())
    assert (extra := buf.get("extra")) is not None
    assert (cutouts := extra.get("LSSTCutoutImages")) is not None
    assert set(cutouts.keys()) == {169676640861290517}, (
        "only one cutout should be retrieved"
    )
    assert (cutout := cutouts.get(169676640861290517)) is not None
    assert all(
        key in cutout for key in ["cutoutScience", "cutoutTemplate", "cutoutDifference"]
    )
    assert isinstance(cutout["cutoutScience"], bytes)
    assert isinstance(cutout["cutoutTemplate"], bytes)
    assert isinstance(cutout["cutoutDifference"], bytes)
