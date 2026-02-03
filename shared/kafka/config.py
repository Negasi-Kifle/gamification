"""
Kafka configuration management.

Loads Kafka settings from environment variables and Django settings.
"""

import os
from dataclasses import dataclass


@dataclass
class KafkaConfig:
    """
    Kafka configuration container.

    Attributes:
        bootstrap_servers: Kafka broker addresses (comma-separated)
        schema_registry_url: URL of the Confluent Schema Registry
        security_protocol: Security protocol (PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL)
        sasl_mechanism: SASL mechanism if using SASL authentication
        sasl_username: SASL username
        sasl_password: SASL password
        ssl_ca_location: Path to CA certificate file
    """

    bootstrap_servers: str
    schema_registry_url: str | None = None
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: str | None = None
    sasl_username: str | None = None
    sasl_password: str | None = None
    ssl_ca_location: str | None = None

    # Topic names
    audit_logs_topic: str = "audit-logs"
    exception_logs_topic: str = "exception-logs"

    @classmethod
    def from_env(cls) -> "KafkaConfig":
        """
        Create KafkaConfig from environment variables.

        Environment variables:
        - KAFKA_BOOTSTRAP_SERVERS (required)
        - SCHEMA_REGISTRY_URL (optional)
        - KAFKA_SECURITY_PROTOCOL (optional, default: PLAINTEXT)
        - KAFKA_SASL_MECHANISM (optional)
        - KAFKA_SASL_USERNAME (optional)
        - KAFKA_SASL_PASSWORD (optional)
        - KAFKA_SSL_CA_LOCATION (optional)
        - AUDIT_LOGS_TOPIC (optional, default: audit-logs)
        - EXCEPTION_LOGS_TOPIC (optional, default: exception-logs)
        """
        return cls(
            bootstrap_servers=os.environ.get(
                "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
            ),
            schema_registry_url=os.environ.get("SCHEMA_REGISTRY_URL"),
            security_protocol=os.environ.get("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
            sasl_mechanism=os.environ.get("KAFKA_SASL_MECHANISM"),
            sasl_username=os.environ.get("KAFKA_SASL_USERNAME"),
            sasl_password=os.environ.get("KAFKA_SASL_PASSWORD"),
            ssl_ca_location=os.environ.get("KAFKA_SSL_CA_LOCATION"),
            audit_logs_topic=os.environ.get("AUDIT_LOGS_TOPIC", "audit-logs"),
            exception_logs_topic=os.environ.get(
                "EXCEPTION_LOGS_TOPIC", "exception-logs"
            ),
        )

    @classmethod
    def from_django_settings(cls) -> "KafkaConfig":
        """
        Create KafkaConfig from Django settings.

        Falls back to environment variables for missing values.
        """
        try:
            from django.conf import settings

            return cls(
                bootstrap_servers=getattr(
                    settings,
                    "KAFKA_BOOTSTRAP_SERVERS",
                    os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
                ),
                schema_registry_url=getattr(
                    settings,
                    "SCHEMA_REGISTRY_URL",
                    os.environ.get("SCHEMA_REGISTRY_URL"),
                ),
                audit_logs_topic=getattr(
                    settings,
                    "AUDIT_LOGS_TOPIC",
                    os.environ.get("AUDIT_LOGS_TOPIC", "audit-logs"),
                ),
                exception_logs_topic=getattr(
                    settings,
                    "EXCEPTION_LOGS_TOPIC",
                    os.environ.get("EXCEPTION_LOGS_TOPIC", "exception-logs"),
                ),
            )
        except ImportError:
            return cls.from_env()

    def to_producer_config(self) -> dict:
        """Convert to confluent-kafka producer configuration dict."""
        config = {
            "bootstrap.servers": self.bootstrap_servers,
        }

        if self.security_protocol != "PLAINTEXT":
            config["security.protocol"] = self.security_protocol

        if self.sasl_mechanism:
            config["sasl.mechanism"] = self.sasl_mechanism

        if self.sasl_username:
            config["sasl.username"] = self.sasl_username

        if self.sasl_password:
            config["sasl.password"] = self.sasl_password

        if self.ssl_ca_location:
            config["ssl.ca.location"] = self.ssl_ca_location

        return config

    def to_consumer_config(self, group_id: str) -> dict:
        """Convert to confluent-kafka consumer configuration dict."""
        config = self.to_producer_config()
        config["group.id"] = group_id
        config["auto.offset.reset"] = "earliest"
        return config
