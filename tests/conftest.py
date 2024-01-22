from itertools import cycle
from pathlib import Path

import mongomock
import pytest

from ampel.abstract.AbsAlertFilter import AbsAlertFilter, AmpelAlertProtocol
from ampel.abstract.AbsAlertLoader import AbsAlertLoader
from ampel.dev.DevAmpelContext import DevAmpelContext


class MockAlertLoader(AbsAlertLoader):
    alerts: list[dict]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._it = iter(self.alerts)

    def _add_metadata(self, alert: dict) -> dict:
        alert["__kafka"] = {"alertId": alert["alertId"]}
        return alert

    def __next__(self):
        return self._add_metadata(next(self._it))


class MockFilter(AbsAlertFilter):
    pattern: list[bool]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._cycle = cycle(self.pattern)

    def process(self, alert: AmpelAlertProtocol) -> None | bool | int:
        return next(self._cycle)


@pytest.fixture()
def _patch_mongo(monkeypatch):
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


@pytest.fixture()
def mock_context(_patch_mongo, testing_config: Path):
    ctx: DevAmpelContext = DevAmpelContext.load(
        config=str(testing_config), purge_db=True
    )
    for c in "ElasticcLong", "ElasticcShort":
        ctx.add_channel(c)
    ctx.register_unit(MockAlertLoader)
    ctx.register_unit(MockFilter)
    return ctx
