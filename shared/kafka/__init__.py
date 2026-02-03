"""
Kafka integration module for the Gamification service.

Provides producer/consumer utilities for event-driven communication
with other services in the Convex ecosystem.

Avro (Kafka / Redpanda):
- Uses Schema Registry for Avro schema management
- Produces/consumes messages to configured topics
- Same schema format as .NET services

Usage:
    from shared.kafka import KafkaProducer, KafkaConsumer

    # Producer
    producer = KafkaProducer()
    producer.produce("topic-name", {"key": "value"}, schema_name="EventName")

    # Consumer
    consumer = KafkaConsumer(["topic-name"], "consumer-group")
    for message in consumer.consume():
        process(message)
"""

from shared.kafka.config import KafkaConfig
from shared.kafka.consumer import KafkaConsumer
from shared.kafka.producer import KafkaProducer
from shared.kafka.serializers import AvroSerializer, JsonSerializer

__all__ = [
    "AvroSerializer",
    "JsonSerializer",
    "KafkaConfig",
    "KafkaConsumer",
    "KafkaProducer",
]
