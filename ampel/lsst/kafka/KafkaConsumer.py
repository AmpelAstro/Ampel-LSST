import bson
import confluent_kafka

from ampel.queue.AbsConsumer import AbsConsumer
from ampel.t2.T2QueueWorker import QueueItem

from .KafkaConsumerBase import KafkaConsumerBase


class KafkaConsumer(KafkaConsumerBase, AbsConsumer[QueueItem]):
    def consume(self) -> None | QueueItem:
        message = self._poll()
        if message is None:
            return None
        item: QueueItem = bson.decode(message.value())  # type: ignore[assignment]
        item["_meta"] = confluent_kafka.TopicPartition(  # type: ignore[typeddict-unknown-key]
            message.topic(), message.partition(), message.offset()
        )
        return item

    def acknowledge(self, message: QueueItem) -> None:
        """
        Store offsets of fully-processed messages
        """
        meta: confluent_kafka.TopicPartition = message["_meta"]  # type: ignore[typeddict-item]
        try:
            self._consumer.store_offsets([meta])
        except confluent_kafka.KafkaException as exc:
            # librdkafka will refuse to store offsets on a partition that is not
            # currently assigned. this can happen if the group is rebalanced
            # while a batch of messages is in flight. see also:
            # https://github.com/confluentinc/confluent-kafka-dotnet/issues/1861
            err = exc.args[0]
            if err.code() != confluent_kafka.KafkaError._STATE:  # noqa: SLF001
                raise
