import logging
from collections.abc import Callable
from typing import Any

from shared.kafka.config import KafkaConfig
from shared.kafka.serializers import AvroSerializer, JsonSerializer, MessageSerializer

logger = logging.getLogger(__name__)


class KafkaProducer:
    """
    Kafka producer for publishing messages.

    Usage:
        producer = KafkaProducer()
        producer.produce("topic-name", {"key": "value"})
        producer.flush()  # Ensure all messages are sent
    """

    def __init__(
        self,
        config: KafkaConfig | None = None,
        serializer: MessageSerializer | None = None,
    ):
        """
        Initialize Kafka producer.

        Args:
            config: Kafka configuration (defaults to from_django_settings)
            serializer: Message serializer (defaults to AvroSerializer if Schema Registry
                       is configured, otherwise JsonSerializer)
        """
        self.config = config or KafkaConfig.from_django_settings()
        self._producer = None

        # Initialize serializer
        if serializer:
            self.serializer = serializer
        elif self.config.schema_registry_url:
            self.serializer = AvroSerializer(self.config.schema_registry_url)
        else:
            self.serializer = JsonSerializer()

        self._init_producer()

    def _init_producer(self) -> None:
        """Initialize the Kafka producer."""
        try:
            from confluent_kafka import Producer

            self._producer = Producer(self.config.to_producer_config())
            logger.info(f"Kafka producer initialized: {self.config.bootstrap_servers}")
        except ImportError:
            logger.warning(
                "confluent-kafka not installed. "
                "Install with: pip install confluent-kafka"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")

    def produce(
        self,
        topic: str,
        value: dict[str, Any],
        key: str | None = None,
        schema_name: str | None = None,
        headers: dict[str, str] | None = None,
        on_delivery: Callable | None = None,
    ) -> bool:
        """
        Produce a message to a Kafka topic.

        Args:
            topic: Topic name
            value: Message value (dict to be serialized)
            key: Optional message key
            schema_name: Optional Avro schema name for serialization
            headers: Optional message headers
            on_delivery: Optional delivery callback function

        Returns:
            True if message was queued successfully, False otherwise
        """
        if not self._producer:
            logger.error("Kafka producer not initialized")
            return False

        try:
            # Serialize value
            serialized_value = self.serializer.serialize(value, schema_name)

            # Prepare headers
            kafka_headers = None
            if headers:
                kafka_headers = [(k, v.encode("utf-8")) for k, v in headers.items()]

            # Produce message
            self._producer.produce(
                topic=topic,
                value=serialized_value,
                key=key.encode("utf-8") if key else None,
                headers=kafka_headers,
                callback=on_delivery or self._default_delivery_callback,
            )

            # Trigger delivery reports for queued messages
            self._producer.poll(0)

            return True

        except Exception as e:
            logger.error(f"Failed to produce message to {topic}: {e}")
            return False

    def flush(self, timeout: float = 10.0) -> int:
        """
        Wait for all messages to be delivered.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            Number of messages still in queue (0 means all delivered)
        """
        if not self._producer:
            return 0

        return self._producer.flush(timeout)

    def _default_delivery_callback(self, err, msg) -> None:
        """Default delivery callback for logging."""
        if err:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def close(self) -> None:
        """Close the producer and flush pending messages."""
        if self._producer:
            self.flush()
            logger.info("Kafka producer closed")


# Singleton instance for convenience
_default_producer: KafkaProducer | None = None


def get_producer() -> KafkaProducer:
    """Get or create the default Kafka producer instance."""
    global _default_producer  # noqa: PLW0603
    if _default_producer is None:
        _default_producer = KafkaProducer()
    return _default_producer


def produce(
    topic: str,
    value: dict[str, Any],
    key: str | None = None,
    schema_name: str | None = None,
    headers: dict[str, str] | None = None,
) -> bool:
    """
    Convenience function to produce a message using the default producer.

    Args:
        topic: Topic name
        value: Message value (dict)
        key: Optional message key
        schema_name: Optional Avro schema name
        headers: Optional message headers

    Returns:
        True if message was queued successfully
    """
    return get_producer().produce(topic, value, key, schema_name, headers)
