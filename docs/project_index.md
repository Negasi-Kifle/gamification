# Project Index

## Overview

This repository contains the Gamification service - a Python (Django) monolith using clean architecture (Domain, Application, Infrastructure) with shared communication patterns (HTTP, gRPC, Kafka) and PostgreSQL for persistence. It is part of a larger microservices ecosystem where other services are built with .NET Core.

## Project Structure

```
gamification/
├── manage.py              # Django CLI entry point
├── config/                # Django project configuration
│   ├── settings.py        # Shared settings for all modules
│   ├── urls.py            # Root URL router
│   ├── wsgi.py            # WSGI entry point
│   └── asgi.py            # ASGI entry point
├── bonus/                 # Bonus module (clean architecture)
│   ├── src/               # Source code
│   │   ├── Domain/        # Entities, value objects, repository interfaces
│   │   ├── Application/   # Use cases, DTOs
│   │   ├── Infrastructure/# Django ORM, repository implementations
│   │   └── Presentation/  # REST views, gRPC servicers
│   └── tests/             # Unit tests for all layers
├── shared/                # Shared code (gRPC protos, server)
│   └── grpc/
│       ├── protos/        # Proto definitions
│       ├── server.py      # gRPC server (registers all module servicers)
│       ├── bonus_pb2.py   # Generated Python code
│       └── bonus_pb2_grpc.py
├── docs/                  # Documentation
└── TODO.md                # Task tracking
```

## Module Map

- `config/`: Django project configuration (single instance for all modules).
- `bonus/`: Bonus module implementation (clean architecture layout inside `bonus/src`).
- `shared/`: Shared utilities, proto definitions, and the gRPC server that registers all module servicers.
- `docs/`: Requirements and schema notes (`technical_requirements.md`, `bonus_config.yaml`).

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
| HTTP/REST | ✅ Implemented | Django views, CSRF exempt for API |
| gRPC | 🟡 Partial | Servicer implemented, server runner missing |
| Kafka | ⚪ Not Started | Required for event-driven communication |

## Dependencies

```
Django==6.0.1
psycopg2-binary==2.9.11
grpcio==1.76.0
grpcio-tools==1.76.0
protobuf==6.33.5
pytest==9.0.2
pytest-django==4.11.1
python-dotenv==1.2.1
```

