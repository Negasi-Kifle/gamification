# Project Index

## Overview

This repository contains the Gamification service - a Python (Django) monolith using clean architecture (Domain, Application, Infrastructure) with shared communication patterns (HTTP, gRPC, Kafka) and PostgreSQL for persistence. It is part of a larger microservices ecosystem where other services are built with .NET Core.

## Project Structure

```
gamification/
├── manage.py              # Django CLI entry point
├── Dockerfile             # Container image definition
├── docker-compose.yml     # Local development environment
├── .gitlab-ci.yml         # CI/CD pipeline
├── pyproject.toml         # Python project config (ruff, pytest)
├── .pre-commit-config.yaml# Pre-commit hooks
├── gamification/          # Django project configuration
│   ├── settings.py        # Shared settings for all modules
│   ├── urls.py            # Root URL router
│   ├── wsgi.py            # WSGI entry point
│   └── asgi.py            # ASGI entry point
├── bonus/                 # Bonus module (clean architecture)
│   ├── src/               # Source code
│   │   ├── Domain/        # Entities, value objects, repository interfaces
│   │   ├── Application/   # Use cases, DTOs, jobs
│   │   ├── Infrastructure/# Django ORM, repository implementations
│   │   └── Presentation/  # REST views, gRPC servicers
│   └── tests/             # Unit tests for all layers
├── shared/                # Shared cross-cutting concerns
│   ├── grpc/              # gRPC server and proto definitions
│   ├── kafka/             # Kafka producer/consumer utilities
│   ├── audit/             # Audit log publishing
│   ├── logging/           # Structured JSON logging
│   ├── middleware/        # Django middleware (correlation IDs)
│   ├── scheduler/         # Scheduler job integration
│   └── tracing/           # OpenTelemetry integration
├── docs/                  # Documentation
│   ├── deploy.md          # Deployment guide
│   └── ...
├── CHANGELOG.md           # Release history
└── TODO.md                # Task tracking
```

## Module Map

- `gamification/`: Django project configuration (single instance for all modules).
- `bonus/`: Bonus module implementation (clean architecture layout inside `bonus/src`).
- `shared/`: Shared cross-cutting concerns:
  - `grpc/`: gRPC server and proto definitions
  - `kafka/`: Kafka producer/consumer for event streaming
  - `audit/`: Audit log and exception log publishing
  - `logging/`: Structured JSON logging with correlation IDs
  - `middleware/`: Django middleware for correlation IDs
  - `scheduler/`: Job dispatcher and scheduler client
  - `tracing/`: OpenTelemetry/Jaeger integration
- `docs/`: Documentation (`technical_requirements.md`, `technical_guideline.md`, `deploy.md`, `bonus_config.yaml`).

## Planned Modules (per technical_requirements.md)

| Module | Status | Description |
|--------|--------|-------------|
| Bonus | 🟡 In Progress | Bonus types, bet rules, deposit/free bet |
| CRM | ⚪ Not Started | User stats (weekly/daily), customer groups |
| Loyalty | ⚪ Not Started | Points wallet, earn from spend, levels & XP |
| Wheel | ⚪ Not Started | Wheels, rewards, spin chances, claims |
| Tournaments | ⚪ Not Started | Campaigns, leaderboards, prizes |
| Campaign/Messaging | ⚪ Not Started | User groups, SMS/Telegram scheduling |
| Marketing | ⚪ Not Started | Campaign attribution and tracking |

## Docs Folder Summary

- `docs/technical_requirements.md`: Service scope (Gamification + CRM), tech stack (Django, PostgreSQL, Docker), communication patterns (HTTP/APISIX, gRPC, Kafka), observability, and clean architecture rules.
- `docs/bonus_config.yaml`: Bonus reward engine schema and campaign trigger/condition definitions. Covers reward types (Casino Freebet, Sport Freebet, Cash, Cash Bonus, In Kind) and BonusCampaign triggers (Sign Up, Deposit, CasinoBet, SportBet).

## Bonus Module Detailed Index

### Layer Overview

| Layer | Path | Responsibility |
|-------|------|----------------|
| Domain | `bonus/src/Domain` | Entities, value objects, repository interfaces, exceptions |
| Application | `bonus/src/Application` | Use cases, request/response DTOs |
| Infrastructure | `bonus/src/Infrastructure` | Django ORM models, repository implementations |
| Presentation (REST) | `bonus/src/Presentation/REST` | HTTP views and URL routing |
| Presentation (gRPC) | `bonus/src/Presentation/grpc` | gRPC servicer implementation |

### Domain (`bonus/src/Domain`)

**Entity**

- `entities/CasinoFreeBet.py`: Core freebet entity with business rules.
  - Validation on creation: name length >= 2, unit value > 0, quantity >= 0, expiry minutes > 0.
  - Status behavior: activate/deactivate with allowed transitions.
  - Expiry logic: `calculate_expiry_time`, `is_expired`, `get_effective_status`.
  - Value logic: `get_total_value`, `can_be_used`.

**Value Objects**

- `value_objects/StatusValueObject.py`: `CasinoFreeBetStatus` enum (ACTIVE, INACTIVE, EXPIRED, USED) with transition rules.
- `value_objects/CurrencyValueObject.py`: `FreebetCurrency` enum (ETB, SZL, TSh, ZMW, USD) with `validate()` helper.

**Repository Interface**

- `repositories/CasinoFreeBetRepositoryInterface.py`: Abstract interface for persistence:
  - `save`, `find_by_id`, `find_by_public_id`, `find_active_by_tenant`, `find_expiring_soon`, `delete`.

**Exceptions**

- `exceptions/CasinoFreeBetExceptions.py`: Domain exceptions:
  - `FreebetError` (base), `InsufficientFreebetsError`, `FreebetExpiredError`, `InvalidFreebetStateError`.

### Application (`bonus/src/Application`)

**Use Cases**

- `use_cases/CreateCasinoFreeBetUsecase.py`: Validates currency, constructs `CasinoFreeBet`, persists via repository, returns response DTO.
- `use_cases/UpdateCasinoFreeBetStatusUsecase.py`: Loads by public ID, blocks expired updates, uses domain transition methods, persists, returns response DTO.
- `use_cases/GetExpiringCasinoFreebetsUseCase.py`: Queries repository for expiring freebets (threshold in hours), returns response DTOs.

**DTOs**

- `dto/request/CasinoCreateFreeBetRequestDto.py`: Input DTO for creation (tenant_id, name, game_id, unit_value, currency, description, quantity, expiry_minutes, initial_status).
- `dto/response/CasinoFreeBetResponseDto.py`: Output DTO with computed fields (public_id, total_value, expires_at, is_expired).

### Infrastructure (`bonus/src/Infrastructure`)

**Django ORM Model**

- `models.py`: `CasinoFreeBetModel` defines DB schema.
  - Fields: public_id (UUID), tenant_id, name, description, currency, game_id, unit_value, quantity, expiry_minutes, status, created_at, updated_at.
  - Indexes: `(tenant_id, status)`, `(created_at, expiry_minutes)`.
  - Table: `bonus_casino_freebet`.

**Repository Implementation**

- `repository/CasinoFreeBetRepository.py`: `DjangoCasinoFreeBetRepository` implements persistence.
  - Uses transactions for save operations.
  - Computes expiry in Python (not stored in DB).
  - Maps between ORM model and domain entity.

**Django App Config**

- `apps.py`: `BonusConfig` Django app configuration with label `bonus`.

### Presentation (REST) (`bonus/src/Presentation/REST`)

**Views**

- `views/casino_freebet/views.py`:
  - `CasinoFreeBetListCreateView`: `GET` lists expiring freebets (hours_threshold query param), `POST` creates freebets.
  - `CasinoFreeBetDetailView`: `PATCH` updates freebet status.
  - Uses request DTOs and corresponding use cases, serializes response DTOs to JSON.

**Routing**

- `urls.py`: Module routes:
  - `casino-freebets/` - List/Create
  - `casino-freebets/<str:public_id>/` - Detail/Update
- `config/urls.py`: Root URL router, includes module routes under `/api/bonus/` prefix.

**Entry Points**

- `manage.py`: Django CLI entry point (project root).
- `config/wsgi.py`, `config/asgi.py`: Django server entry points.

### Presentation (gRPC) (`bonus/src/Presentation/grpc`)

**Servicer**

- `CasinoFreeBetServicer.py`: gRPC handler implementing `CasinoFreeBetService`.
  - `CreateFreebet`: Creates new freebet via use case.
  - `UpdateStatus`: Updates freebet status (activate/deactivate).
  - `GetExpiring`: Returns freebets expiring within threshold.
  - Includes currency/status enum mapping from proto values to domain enums.

**Proto Definition**

- `shared/grpc/protos/bonus.proto`: Service and message definitions.
  - Service: `CasinoFreeBetService` with `CreateFreebet`, `UpdateStatus`, `GetExpiring` RPCs.
  - Enums: `CasinoFreeBetStatus`, `FreebetCurrency`.
  - Messages: `CreateFreebetRequest`, `UpdateStatusRequest`, `GetExpiringRequest`, `FreebetResponse`, `FreebetListResponse`.

### Module Exports

- `bonus/src/__init__.py` re-exports all public symbols from Domain, Application, Infrastructure, and Presentation layers.

### Tests (`bonus/tests`)

- `test_domain.py`: Unit tests for entity validation, status transitions, expiry logic, value calculations.
- `test_application.py`: Unit tests for use cases with mock repository.
- `test_infrastructure.py`: Unit tests for repository mapping and ORM integration (DB tests skipped, require pytest-django setup).

### Configuration

- `requirements.txt`: Project dependencies (Django 6.0.1, psycopg2-binary, grpcio, grpcio-tools, protobuf, pytest, pytest-django, python-dotenv).
- `.env`: Environment variables for database and Django settings (not committed).
- `pytest.ini`: Pytest configuration for test discovery.

## Communication Patterns

| Pattern | Status | Notes |
|---------|--------|-------|
| HTTP/REST | ✅ Implemented | Django views with correlation ID middleware |
| gRPC | ✅ Implemented | Server in `shared/grpc/server.py`, servicers registered |
| Kafka | ✅ Implemented | Producer/consumer in `shared/kafka/`, Avro support |

## Infrastructure Components

| Component | Status | Notes |
|-----------|--------|-------|
| Docker | ✅ Implemented | Dockerfile, docker-compose.yml |
| CI/CD | ✅ Implemented | GitLab CI with lint, test, build stages |
| Structured Logging | ✅ Implemented | JSON format with correlation IDs |
| Audit Logging | ✅ Implemented | Publishes to audit-logs, exception-logs topics |
| Scheduler Integration | ✅ Implemented | Job dispatcher in Application layer |
| Tracing | ✅ Implemented | OpenTelemetry with Jaeger exporter |
| Migration Linting | ✅ Implemented | django-migration-linter integrated |

## Shared Module Index

### `shared/logging/`
Structured JSON logging per guideline §9.
- `formatter.py`: JsonFormatter with standard fields (timestamp, level, event, trace_id, request_id, tenant_id, service)
- `context.py`: LogContext for managing correlation IDs

### `shared/middleware/`
Django middleware per guideline §9.
- `correlation.py`: CorrelationIdMiddleware extracts/generates request_id, trace_id, tenant_id

### `shared/kafka/`
Kafka integration per guideline §5, §6.
- `config.py`: KafkaConfig from environment
- `producer.py`: KafkaProducer with Avro serialization
- `consumer.py`: KafkaConsumer for event handling
- `serializers.py`: AvroSerializer, JsonSerializer

### `shared/audit/`
Audit logging per guideline §6.
- `models.py`: AuditLogMessage, ExceptionLogMessage
- `publisher.py`: AuditPublisher, ExceptionPublisher

### `shared/scheduler/`
Scheduler integration per guideline §8.
- `dispatcher.py`: JobDispatcher maps job names to handlers
- `client.py`: SchedulerClient for reporting job status

### `shared/tracing/`
OpenTelemetry integration per tech requirements.
- `setup.py`: init_tracing with Jaeger exporter
- `utils.py`: create_span, get_current_trace_id

## Dependencies

```
# Django Framework
Django==6.0.1
gunicorn==23.0.0

# Database
psycopg2-binary==2.9.11

# gRPC
grpcio==1.76.0
grpcio-tools==1.76.0
protobuf==6.33.5

# Kafka
confluent-kafka==2.3.0
fastavro==1.9.3

# OpenTelemetry
opentelemetry-api==1.22.0
opentelemetry-sdk==1.22.0
opentelemetry-instrumentation-django==0.43b0
opentelemetry-instrumentation-grpc==0.43b0
opentelemetry-exporter-jaeger==1.21.0

# Testing
pytest==9.0.2
pytest-django==4.11.1
coverage==7.4.0

# Linting & Formatting
ruff==0.3.0
pre-commit==3.6.0
bandit==1.7.7
django-migration-linter==5.1.0

# Configuration
python-dotenv==1.2.1
```
