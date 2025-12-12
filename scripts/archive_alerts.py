"""
Read alerts stored in Confluent Wire Format in a Kafka topic, and write them to
a tar archive alongside a JSON representation of the schema.
"""

import datetime
import io
import json
import logging
import os
import struct
import tarfile
import time
from argparse import ArgumentParser
from pathlib import Path

import fastavro
from confluent_kafka import Consumer, TopicPartition
from confluent_kafka.admin import AdminClient
from confluent_kafka.schema_registry.avro import (
    AvroDeserializer,
    SchemaRegistryClient,
    SerializationContext,
)
from confluent_kafka.serialization import MessageField
from fastavro import schemaless_writer

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def consume_range(
    consumer: Consumer,
    toppars: list[TopicPartition],
    start: datetime.datetime,
    end: datetime.datetime,
    timeout: float = 30.0,
):
    # Get offset of first message newer than start time (-1 if not found)
    start_offset = {
        (tp.topic, tp.partition): tp.offset
        for tp in consumer.offsets_for_times(
            [
                TopicPartition(
                    t.topic, t.partition, offset=int(start.timestamp() * 1_000)
                )
                for t in toppars
            ]
        )
    }
    # Get offset of first message older than end time (-1 if not found)
    end_offset = {
        (tp.topic, tp.partition): tp.offset
        for tp in consumer.offsets_for_times(
            [
                TopicPartition(
                    t.topic, t.partition, offset=int(end.timestamp() * 1_000)
                )
                for t in toppars
            ]
        )
    }

    # Assign partitions with nonempty range
    consumer.assign(
        [
            TopicPartition(tp.topic, tp.partition, start_offset)
            for (start_offset, end_offset, tp) in zip(
                start_offset.values(),
                end_offset.values(),
                toppars,
                strict=True,
            )
            if start_offset != end_offset
        ]
    )
    # Use latest offset when there are no messages newer than end time
    total = 0
    for tp in consumer.assignment():
        key = (tp.topic, tp.partition)
        if end_offset[key] == -1:
            end_offset[key] = consumer.get_watermark_offsets(tp)[-1]
        total += end_offset[key] - start_offset[key]
    log.info(
        f"{total} messages in {set(tp.topic for tp in consumer.assignment())} {start}--{end}"
    )

    messages = 0
    bytes = 0

    t0 = time.time()

    try:
        while True:
            if not consumer.assignment():
                return
            for _ in range(10):
                msg = consumer.poll(timeout / 10)
                if msg:
                    break
            if not msg:
                break
            messages += 1
            bytes += len(msg.value())
            yield msg
            if msg.offset() >= end_offset[msg.topic(), msg.partition()] - 1:
                tp = TopicPartition(msg.topic(), msg.partition())
                consumer.incremental_unassign([tp])
                log.debug(f"Finished {tp}, {len(consumer.assignment())} remaining")
    finally:
        dt = time.time() - t0
        log.info(
            f"Consumed {messages} messages ({bytes / (1 << 20):.0f} MB) in {dt:.2f} seconds ({bytes / (1 << 20) / dt:.2f} MB/s, {messages / dt:.2f} msg/s)"
        )
        consumer.unassign()


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--topic", type=str, default="lsst-alerts-v9.0")
    parser.add_argument(
        "--broker", type=str, default="usdf-alert-stream-dev.lsst.cloud:9094"
    )
    parser.add_argument(
        "--schema-registry",
        type=str,
        default="https://usdf-alert-schemas-dev.slac.stanford.edu",
    )
    parser.add_argument(
        "--username", type=str, default=os.environ.get("KAFKA_USERNAME")
    )
    parser.add_argument(
        "--password", type=str, default=os.environ.get("KAFKA_PASSWORD")
    )
    parser.add_argument(
        "--keep-cutouts",
        default=False,
        action="store_true",
        help="Keep image cutouts in archived alerts",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--days-ago", type=int, help="Days ago to archive")
    group.add_argument(
        "--date",
        type=lambda s: datetime.datetime.strptime(s, "%Y-%m-%d").replace(
            tzinfo=datetime.UTC
        ),
    )
    args = parser.parse_args()

    consumer = Consumer(
        {
            "bootstrap.servers": args.broker,
            "group.id": f"{args.username}-archive",
            "enable.auto.commit": True,
            "enable.auto.offset.store": False,
            "enable.partition.eof": False,  # don't emit messages on EOF
            "security.protocol": "SASL_PLAINTEXT",
            "sasl.mechanism": "SCRAM-SHA-512",
            "sasl.username": args.username,
            "sasl.password": args.password,
            "auto.offset.reset": "earliest",
        }
    )

    ac = AdminClient(
        {
            "bootstrap.servers": args.broker,
            "security.protocol": "SASL_PLAINTEXT",
            "sasl.mechanism": "SCRAM-SHA-512",
            "sasl.username": args.username,
            "sasl.password": args.password,
        }
    )

    registry_client = SchemaRegistryClient(
        {
            "url": args.schema_registry,
        }
    )
    deserializer = AvroDeserializer(registry_client)

    topic = args.topic
    start = (
        datetime.datetime(
            *datetime.datetime.now(datetime.UTC).timetuple()[:3],
            tzinfo=datetime.UTC,
        )
        - datetime.timedelta(days=args.days_ago)
        if args.days_ago is not None
        else args.date
    )
    end = start + datetime.timedelta(days=1)

    output = (
        Path(topic)
        / f"{start.year:04d}"
        / f"{start.month:02d}"
        / start.strftime("%Y-%m-%d.tar.gz")
    )
    if not output.parent.exists():
        output.parent.mkdir(parents=True)

    toppars = [
        TopicPartition(tm.topic, pm.id)
        for tm in ac.list_topics(topic).topics.values()
        for pm in tm.partitions.values()
    ]

    last_schema_id = -1
    schema = {}

    count = 0

    with tarfile.open(output, "w:gz") as tar:
        for msg in consume_range(consumer, toppars, start, end, timeout=30):
            ctx = SerializationContext(msg.topic(), MessageField.VALUE, msg.headers())
            magic, schema_id = struct.unpack(">bI", msg.value()[:5])
            if schema_id != last_schema_id:
                last_schema_id = schema_id
                schema_str = registry_client.get_schema(schema_id).schema_str
                schema = fastavro.parse_schema(json.loads(schema_str))
                ti = tarfile.TarInfo(name="schema.json")
                ti.size = len(schema_str.encode("utf-8"))
                ti.mtime = time.time()
                tar.addfile(ti, io.BytesIO(schema_str.encode("utf-8")))

            alert = {
                k: v
                for k, v in deserializer(msg.value(), ctx).items()
                if args.keep_cutouts or not k.startswith("cutout")
            }

            with io.BytesIO() as alertbuf:
                schemaless_writer(alertbuf, schema, alert)
                alertbuf.seek(0)
                ti = tarfile.TarInfo(
                    name=f"{msg.partition():02d}_{msg.offset():010d}.avro"
                )
                ti.size = len(alertbuf.getvalue())
                ti.mtime = msg.timestamp()[-1] / 1_000
                tar.addfile(ti, alertbuf)

            count += 1

            if count % 100 == 0:
                log.info(f"Processed {count} messages")
    log.info(f"{output}: {os.stat(output).st_size / (1 << 20):.1f} MB")
