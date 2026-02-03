# Changelog

All notable changes to the Gamification service will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Docker support: Dockerfile and docker-compose.yml for containerized deployment
- Structured JSON logging with correlation IDs (request_id, trace_id, tenant_id)
- Correlation ID middleware for Django REST and gRPC
- Pre-commit hooks with ruff linter and formatter
- Kafka producer/consumer utilities in `shared/kafka/`
- Audit log publisher for `audit-logs` and `exception-logs` topics
- Scheduler integration with job dispatcher
- Django migration linter integration
- GitLab CI/CD configuration
- `.env.example` template for environment configuration
- OpenTelemetry integration for distributed tracing

### Changed

- Updated requirements.txt with all new dependencies
- Added correlation middleware to Django MIDDLEWARE setting
- Added LOGGING configuration to settings.py

## [0.1.0] - 2026-02-03

### Added

- Initial project structure with clean architecture
- Bonus module with CasinoFreeBet entity
- Domain layer: entities, value objects, repository interfaces, exceptions
- Application layer: use cases, DTOs, request/response models
- Infrastructure layer: Django ORM models, repository implementations
- Presentation layer: REST views, gRPC servicer
- gRPC server entry point in `shared/grpc/server.py`
- Proto definitions for CasinoFreeBetService
- Unit tests for all layers
- Health check endpoint at `/api/bonus/health/`

### Technical Details

- Django 6.0.1
- PostgreSQL for persistence
- gRPC for inter-service communication
- Clean architecture with Domain, Application, Infrastructure, Presentation layers

---

## Version Guidelines

When releasing a new version:

1. Update this CHANGELOG with all changes since the last release
2. Categorize changes: Added, Changed, Deprecated, Removed, Fixed, Security
3. Tag the commit with the version number (e.g., `v0.2.0`)
4. Update `docs/deploy.md` if deployment steps have changed
