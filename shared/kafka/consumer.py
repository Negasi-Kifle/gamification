import logging
from collections.abc import Callable, Generator
from dataclasses import dataclass, field
from typing import Any

from shared.kafka.config import KafkaConfig
from shared.kafka.serializers import AvroSerializer, JsonSerializer, MessageSerializer

logger = logging.getLogger(__name__)


@dataclass(repr=False)
class KafkaMessage:
    """
    Wrapper for consumed Kafka messages.

    Attributes:
        topic: Topic name
        partition: Partition number
        offset: Message offset
        key: Message key (if any)
        value: Deserialized message value
        headers: Message headers
        timestamp: Message timestamp
    """

    topic: str
    partition: int
    offset: int
    key: str | None
    value: dict[str, Any]
    headers: dict[str, str] = field(default_factory=dict)
    timestamp: int | None = None

    def __repr__(self) -> str:
        return f"KafkaMessage(topic={self.topic}, partition={self.partition}, offset={self.offset})"


class KafkaConsumer:
    """
    Kafka consumer for receiving messages.

    Usage:
        consumer = KafkaConsumer(["topic-name"], "consumer-group")

        # Iterate over messages
        for message in consumer.consume():
            process(message)

        # Or consume with callback
        consumer.consume_with_callback(process_message)
    """

    def __init__(
        self,
        topics: list[str],
        group_id: str,
        config: KafkaConfig | None = None,
        serializer: MessageSerializer | None = None,
    ):
        """
        Initialize Kafka consumer.

        Args:
            topics: List of topics to subscribe to
            group_id: Consumer group ID
            config: Kafka configuration (defaults to from_django_settings)
            serializer: Message serializer (defaults to AvroSerializer if Schema Registry
                       is configured, otherwise JsonSerializer)
        """
        self.topics = topics
        self.group_id = group_id
        self.config = config or KafkaConfig.from_django_settings()
        self._consumer = None
        self._running = False

        # Initialize serializer
        if serializer:
            self.serializer = serializer
        elif self.config.schema_registry_url:
            self.serializer = AvroSerializer(self.config.schema_registry_url)
        else:
            self.serializer = JsonSerializer()

        self._init_consumer()

    def _init_consumer(self) -> None:
        """Initialize the Kafka consumer."""
        try:
            from confluent_kafka import Consumer

            self._consumer = Consumer(self.config.to_consumer_config(self.group_id))
            self._consumer.subscribe(self.topics)
            logger.info(f"Kafka consumer initialized for topics: {self.topics}")
        except ImportError:
            logger.warning(
                "confluent-kafka not installed. "
                "Install with: pip install confluent-kafka"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {e}")

    def consume(
        self,
        timeout: float = 1.0,
        max_messages: int | None = None,
    ) -> Generator[KafkaMessage, None, None]:
        """
        Consume messages from subscribed topics.

        Args:
            timeout: Poll timeout in seconds
            max_messages: Maximum number of messages to consume (None for infinite)

        Yields:
            KafkaMessage objects
        """
        if not self._consumer:
            logger.error("Kafka consumer not initialized")
            return

        self._running = True
        count = 0

        try:
            while self._running:
                if max_messages and count >= max_messages:
                    break

                msg = self._consumer.poll(timeout)

                if msg is None:
                    continue

                if msg.error():
                    logger.error(f"Consumer error: {msg.error()}")
                    continue

                try:
                    # Deserialize value
                    value = self.serializer.deserialize(msg.value())

                    # Parse headers
                    headers = {}
                    if msg.headers():
                        headers = {k: v.decode("utf-8") for k, v in msg.headers()}

                    # Create message wrapper
                    kafka_message = KafkaMessage(
                        topic=msg.topic(),
                        partition=msg.partition(),
                        offset=msg.offset(),
                        key=msg.key().decode("utf-8") if msg.key() else None,
                        value=value,
                        headers=headers,
                        timestamp=msg.timestamp()[1] if msg.timestamp() else None,
                    )

                    count += 1
                    yield kafka_message

                except Exception as e:
                    logger.error(f"Failed to process message: {e}")

        finally:
            self._running = False

    def consume_with_callback(
        self,
        callback: Callable[[KafkaMessage], None],
        timeout: float = 1.0,
        max_messages: int | None = None,
    ) -> None:
        """
        Consume messages and process with callback.

        Args:
            callback: Function to call for each message
            timeout: Poll timeout in seconds
            max_messages: Maximum number of messages to consume
        """
        for message in self.consume(timeout, max_messages):
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Callback error for message {message}: {e}")

    def stop(self) -> None:
        """Stop consuming messages."""
        self._running = False

    def close(self) -> None:
        """Close the consumer."""
        self.stop()
        if self._consumer:
            self._consumer.close()
            logger.info("Kafka consumer closed")

    def commit(self, asynchronous: bool = True) -> None:
        """
        Commit current offsets.

        Args:
            asynchronous: If True, commit asynchronously
        """
        if self._consumer:
            self._consumer.commit(asynchronous=asynchronous)
