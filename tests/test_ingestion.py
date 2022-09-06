from pathlib import Path

import yaml
import pytest
import mongomock
import fastavro

from itertools import cycle

from ampel.dev.DevAmpelContext import DevAmpelContext
from ampel.model.UnitModel import UnitModel
from ampel.alert.AlertConsumer import AlertConsumer
from ampel.abstract.AbsAlertLoader import AbsAlertLoader
from ampel.abstract.AbsAlertFilter import AbsAlertFilter, AmpelAlertProtocol


class MockAlertLoader(AbsAlertLoader):
    alerts: list[dict]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._it = iter(self.alerts)

    def __next__(self):
        return next(self._it)


class MockFilter(AbsAlertFilter):

    pattern: list[bool]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._cycle = cycle(self.pattern)

    def process(self, alert: AmpelAlertProtocol) -> None | bool | int:
        return next(self._cycle)


@pytest.fixture
def patch_mongo(monkeypatch):
    monkeypatch.setattr(
        "ampel.core.AmpelDB.MongoClient", mongomock.MongoClient
    )
    # ignore codec_options in DataLoader
    monkeypatch.setattr(
        "mongomock.codec_options.is_supported", lambda *args: None
    )


@pytest.fixture(scope="session")
def testing_config():
    return Path(__file__).parent / "test-data" / "testing-config.yaml"


@pytest.fixture
def mock_context(patch_mongo, testing_config: Path):
    ctx: DevAmpelContext = DevAmpelContext.load(
        config=str(testing_config), purge_db=True
    )
    for c in "ElasticcLong", "ElasticcShort":
        ctx.add_channel(c)
    ctx.register_unit(MockAlertLoader)
    ctx.register_unit(MockFilter)
    return ctx


def test_muxer(mock_context: DevAmpelContext):
    """
    A point T2 bound to a specific datapoint appears for both channels, even
    when the alert where the target datapoint first appeared was accepted by
    only one channel.
    """

    with (
        Path(__file__).parent / "test-data" / "elasticc-consumer.yml"
    ).open() as f:
        model = UnitModel(**yaml.safe_load(f))
    # alerts from a single diaObject
    with (
        Path(__file__).parent / "test-data" / "11290844.avro"
    ).open("rb") as f:
        alerts = list(fastavro.reader(f))[:2]
    model.config["supplier"]["config"]["loader"] = UnitModel(
        unit="MockAlertLoader", config={"alerts": alerts}
    )
    # accept first alert in one channel only
    model.config["directives"][0]["filter"] = UnitModel(
        unit="MockFilter", config={"pattern": [True, True]}
    )
    model.config["directives"][1]["filter"] = UnitModel(
        unit="MockFilter", config={"pattern": [False, True]}
    )

    processor = mock_context.loader.new_context_unit(
        model=model,
        context=mock_context,
        sub_type=AlertConsumer,
    )
    processor.iter_max = 1

    # insert datapoints from first alert into the database
    assert processor.run() == 1
    # inserts datapoints unique to second alert
    assert processor.run() == 1

    assert (
        len(mock_context.db.get_collection("stock").find_one()["channel"]) == 2
    ), "stock in both channels"
    assert (
        len(
            docs := list(
                mock_context.db.get_collection("t2").find(
                    {"unit": "T2GetDiaObject"}
                )
            )
        )
        == 1
    ), "single point T2 doc found"
    assert len(set(docs[0]["channel"])) == 2, "t2 doc in both channels"
