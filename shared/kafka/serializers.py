"""
Message serializers for Kafka.

Supports:
- JSON serialization (fallback)
- Avro serialization with Schema Registry (recommended)
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class MessageSerializer(ABC):
    """Abstract base class for message serializers."""

    @abstractmethod
    def serialize(self, data: dict[str, Any], schema_name: str | None = None) -> bytes:
        """Serialize data to bytes."""
        pass

    @abstractmethod
    def deserialize(
        self, data: bytes, schema_name: str | None = None
    ) -> dict[str, Any]:
        """Deserialize bytes to dict."""
        pass


class JsonSerializer(MessageSerializer):
    """
    JSON serializer for Kafka messages.

    Use as fallback when Schema Registry is not available.
    Note: Avro with Schema Registry is preferred per guideline §5.
    """

    def serialize(self, data: dict[str, Any], schema_name: str | None = None) -> bytes:
        """Serialize dict to JSON bytes."""
        return json.dumps(data, default=str).encode("utf-8")

    def deserialize(
        self, data: bytes, schema_name: str | None = None
    ) -> dict[str, Any]:
        """Deserialize JSON bytes to dict."""
        return json.loads(data.decode("utf-8"))


class AvroSerializer(MessageSerializer):
    """
    Avro serializer with Schema Registry integration.

    - Uses Schema Registry for schema management
    - Ensures compatibility between producers and consumers
    - Same schema format as .NET services

    Requires:
    - confluent-kafka[avro] or fastavro
    - Schema Registry URL configured
    """

    def __init__(self, schema_registry_url: str | None = None):
        """
        Initialize Avro serializer.

        Args:
            schema_registry_url: URL of the Schema Registry
        """
        self.schema_registry_url = schema_registry_url
        self._schema_registry_client = None
        self._serializer_cache: dict[str, Any] = {}
        self._deserializer_cache: dict[str, Any] = {}

        if schema_registry_url:
            self._init_schema_registry()

    def _init_schema_registry(self) -> None:
        """Initialize Schema Registry client."""
        try:
            from confluent_kafka.schema_registry import SchemaRegistryClient

            self._schema_registry_client = SchemaRegistryClient(
                {"url": self.schema_registry_url}
            )
            logger.info(f"Connected to Schema Registry at {self.schema_registry_url}")
        except ImportError:
            logger.warning(
                "confluent-kafka[avro] not installed. "
                "Install with: pip install confluent-kafka[avro]"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Schema Registry: {e}")

    def serialize(self, data: dict[str, Any], schema_name: str | None = None) -> bytes:
        """
        Serialize dict to Avro bytes.

        Falls back to JSON if Schema Registry is not available.
        """
        if not self._schema_registry_client or not schema_name:
            # Fallback to JSON
            return JsonSerializer().serialize(data)

        try:
            from confluent_kafka.schema_registry.avro import (
                AvroSerializer as ConfluentAvroSerializer,
            )

            if schema_name not in self._serializer_cache:
                # Get or register schema
                schema_str = self._get_schema(schema_name)
                if schema_str:
                    self._serializer_cache[schema_name] = ConfluentAvroSerializer(
                        self._schema_registry_client,
                        schema_str,
                    )

            serializer = self._serializer_cache.get(schema_name)
            if serializer:
                return serializer(data, None)

            # Fallback to JSON if schema not found
            return JsonSerializer().serialize(data)

        except ImportError:
            return JsonSerializer().serialize(data)
        except Exception as e:
            logger.error(f"Avro serialization failed: {e}")
            return JsonSerializer().serialize(data)

    def deserialize(
        self, data: bytes, schema_name: str | None = None
    ) -> dict[str, Any]:
        """
        Deserialize Avro bytes to dict.

        Falls back to JSON if Schema Registry is not available.
        """
        if not self._schema_registry_client or not schema_name:
            return JsonSerializer().deserialize(data)

        try:
            from confluent_kafka.schema_registry.avro import (
                AvroDeserializer as ConfluentAvroDeserializer,
            )

            if schema_name not in self._deserializer_cache:
                schema_str = self._get_schema(schema_name)
                if schema_str:
                    self._deserializer_cache[schema_name] = ConfluentAvroDeserializer(
                        self._schema_registry_client,
                        schema_str,
                    )

            deserializer = self._deserializer_cache.get(schema_name)
            if deserializer:
                return deserializer(data, None)

            return JsonSerializer().deserialize(data)

        except ImportError:
            return JsonSerializer().deserialize(data)
        except Exception as e:
            logger.error(f"Avro deserialization failed: {e}")
            return JsonSerializer().deserialize(data)

    def _get_schema(self, schema_name: str) -> str | None:
        """Get schema from Schema Registry by subject name."""
        if not self._schema_registry_client:
            return None

        try:
            # Subject name convention: {schema_name}-value
            subject = f"{schema_name}-value"
            latest_version = self._schema_registry_client.get_latest_version(subject)
            return latest_version.schema.schema_str
        except Exception as e:
            logger.warning(f"Schema not found for {schema_name}: {e}")
            return None
