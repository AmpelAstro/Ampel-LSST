from pathlib import Path

import fastavro
import pytest
import yaml

from ampel.alert.AlertConsumer import AlertConsumer
from ampel.base.AuxUnitRegister import AuxUnitRegister
from ampel.dev.DevAmpelContext import DevAmpelContext
from ampel.lsst.alert.LSSTAlertSupplier import LSSTAlertSupplier
from ampel.model.UnitModel import UnitModel


@pytest.fixture
def alert_consumer(mock_context: DevAmpelContext) -> AlertConsumer:
    with (
        Path(__file__).parent / "test-data" / "elasticc-consumer.yml"
    ).open() as f:
        model = UnitModel(**yaml.safe_load(f))
    # alerts from a single diaObject
    with (Path(__file__).parent / "test-data" / "11290844.avro").open(
        "rb"
    ) as f:
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

    return processor


def test_muxer(
    mock_context: DevAmpelContext, alert_consumer: AlertConsumer, mocker
):
    """
    A point T2 bound to a specific datapoint appears for both channels, even
    when the alert where the target datapoint first appeared was accepted by
    only one channel.
    """

    alert_consumer.iter_max = 1

    # insert datapoints from first alert into the database
    assert alert_consumer.run() == 1
    # inserts datapoints unique to second alert
    assert alert_consumer.run() == 1

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


def test_message_ack(alert_consumer: AlertConsumer, mocker):
    """
    Alerts are explicitly acknowledged back to the loader
    """
    ack = mocker.patch.object(
        alert_consumer.alert_supplier.alert_loader, "acknowledge"
    )

    assert alert_consumer.run() == 2

    assert ack.call_count == 1, "exactly one batch of acks"
    # NB: alerts may be acked in arbitrary order
    alerts = sorted(ack.call_args[0][0], key=lambda d: d["__kafka"]["alertId"])
    assert len(alerts) == 2
    assert alerts == [
        {"__kafka": {"alertId": alert["alertId"]}}
        for alert in alert_consumer.alert_supplier.alert_loader.alerts
    ], "alerts acked"


def test_duplicate_datapoints(mock_context: DevAmpelContext):
    """
    Alerts that contain differential and forced photometry with the same id
    result in states with unique datapoints.
    """

    with (
        Path(__file__).parent / "test-data" / "elasticc-consumer.yml"
    ).open() as f:
        model = UnitModel(**yaml.safe_load(f))
    # alert with duplicated datapoints
    model.config["supplier"]["config"]["loader"] = UnitModel(
        unit="ElasticcDirAlertLoader",
        config={
            "folder": str(Path(__file__).parent / "test-data"),
            # extension gets translated into .*{extension}
            "extension": "1120_obj104044681_src208089362038.avro.gz",
            "avro_schema": "https://raw.githubusercontent.com/LSSTDESC/elasticc/c47fbd301b87f915c77ac0046d7845c68c306444/alert_schema/elasticc.v0_9.alert.avsc",
        },
    )

    supplier = AuxUnitRegister.new_unit(
        model=UnitModel(**model.config["supplier"]), sub_type=LSSTAlertSupplier
    )
    alert = next(supplier)
    assert len(alert.datapoints) == 20

    processor = mock_context.loader.new_context_unit(
        model=model,
        context=mock_context,
        sub_type=AlertConsumer,
        raise_exc=True,
    )
    processor.iter_max = 1

    # insert datapoints from first alert into the database
    assert processor.run() == 1

    assert (t1 := mock_context.db.get_collection("t1").find_one())
    assert len(t1["dps"]) == len(
        set(t1["dps"])
    ), "datapoints in state are unique"
    assert (
        len(t1["dps"]) < len(alert.datapoints) - 1
    ), "some alert datapoints eliminated"
