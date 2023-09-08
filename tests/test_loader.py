import datetime
import io
from pathlib import Path

import confluent_kafka
import fastavro
import pytest
from pytest_mock import MockerFixture

from ampel.lsst.alert.LSSTAlertSupplier import LSSTAlertSupplier
from ampel.model.UnitModel import UnitModel


class MockMessage:
    """
    Mockup of confluent_kafka.Message, which can't be instantiated from Python
    """
    def __init__(self, record: dict, schema: dict, offset: int):
        buf = io.BytesIO()
        fastavro.schemaless_writer(buf, schema, record)
        self._value = buf.getvalue()
        self._offset = offset
        self._timestamp = confluent_kafka.TIMESTAMP_CREATE_TIME, int(
            datetime.datetime.now().timestamp() * 1000
        )

    def value(self):
        return self._value

    def error(self):
        return None

    def key(self):
        return None

    def topic(self):
        return "topic"

    def partition(self):
        return 0

    def offset(self):
        return self._offset

    def timestamp(self):
        return self._timestamp


@pytest.fixture
def test_alerts():
    """Turn alerts back into Kafka messages"""
    with (Path(__file__).parent / "test-data" / "11290844.avro").open(
        "rb"
    ) as f:
        reader = fastavro.reader(f)
        return reader.writer_schema, [
            MockMessage(record, reader.writer_schema, offset)
            for offset, record in enumerate(reader)
        ]


def test_loader_ack(
    mocker: MockerFixture,
    mock_context,
    test_alerts: tuple[dict, list[MockMessage]],
):
    """
    LSSTAlertLoader acknowledges alerts back to AllConsumingConsumer
    """
    schema, messages = test_alerts

    supplier = LSSTAlertSupplier(
        deserialize=None,
        loader=UnitModel(
            unit="KafkaAlertLoader",
            config={
                "bootstrap": "foo",
                "topics": ["topic"],
                "avro_schema": schema,
            },
        ),
    )

    mock_consumer = mocker.patch.object(
        supplier.alert_loader._consumer, "_consumer"
    )
    mock_consumer.poll.side_effect = messages

    assert supplier.alert_loader._consumer._consumer is mock_consumer

    alerts = list(supplier)
    assert len(alerts) == 3

    assert supplier.alert_loader._consumer._offsets == {("topic", 0): 2}
    assert not mock_consumer.store_offsets.called
    assert not mock_consumer.commit.called

    def verify_offset(offset):
        offsets = mock_consumer.store_offsets.call_args[1]["offsets"]
        assert len(offsets) == 1
        toppar = offsets[0]
        assert toppar.topic == "topic"
        assert toppar.partition == 0
        assert toppar.offset == offset

    supplier.acknowledge(iter(alerts[:2]))
    assert mock_consumer.store_offsets.called
    # offset is at the second alert, even though all have been consumed
    verify_offset(2)

    supplier.acknowledge(reversed(alerts))
    assert mock_consumer.store_offsets.call_count == 2
    # offset is at the last alert, even though acks came out of order
    verify_offset(3)
