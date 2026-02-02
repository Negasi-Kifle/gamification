# Gamification & CRM Service

## For developers

### Scope: Gamification and CRM only. Other services are not named here.

### Tech

This service: Django (Python), clean architecture.
DB: PostgreSQL.
Deploy: Docker (must use).
Other services: .NET Core (C#).
We talk: HTTP (APISIX), gRPC. Events: Kafka (same schema for all).
Same .proto and schema for Django and .NET.
Logger: structured logging. Tracing: Jaeger. OpenTelemetry: spans, metrics.
Unit tests: mandatory. All new and changed code must have unit tests before
merge.

## Quick view

What we build — Gamification + CRM service.
Who uses it — Internal and external (APISIX). Same APIs.
Communication — HTTP, gRPC, Kafka (see section below).
Done by others — Auth, affiliate, big reports (see Domains & features;
Communication).
Notification — We use the notification service (see below).
Shared formats — Same .proto and schema.
Observability — Logger, Jaeger (tracing), OpenTelemetry (spans, metrics).

## Domains & features

Our areas: what each does and other names. If it’s not here, another service does it.
CRM — User stats (weekly/daily), customer groups. Other names: day streaks,
habits.
Loyalty — Points wallet; earn from spend; turn points into balance. Other
names: levels & XP, milestone rewards, codes.
Bonus — Bonus types, bet rules, deposit/free bet. Other names: achievements,
badges, milestone rewards.
Wheel — Wheels, rewards, spin chances, claims. Other names: spin to win,
achievements, milestone rewards.
Tournaments — Campaigns, leaderboards, prizes. Other names: leaderboards
(weekly, competition).
Campaign / Messaging — User groups, SMS/Telegram, send or schedule.
Marketing — Where users came from; campaign names.
Other services — Referrals, invites (affiliate). Auth, permissions (identity).

### Communication (who talks to whom, how)

Clients or APISIX call us — HTTP (REST). Public APIs.
Other services and us — gRPC. Same .proto.
Events — Kafka. Same schema (Avro).
We call identity (auth) — gRPC. Other service.
Big reports — gRPC only. Same report .proto.
Notification service — gRPC or HTTP. SMS, push, etc.
Notification service — how to use
We use the notification service for messages (SMS, Telegram, push). We don’t send ourselves.
1stSame format — Same .proto or HTTP API as other services.
2ndCall — gRPC or HTTP. Send: recipient, channel (SMS/Telegram/push),
message, extra data if needed.
3rdOr events — Publish to Kafka (same schema). Notification service reads and
sends. Use when async.
4thWe don’t send — All sending via notification service.

### Clean architecture (like .NET)
Same layers and rules in Django and .NET.

#### Rules
1stInner parts don’t know outer parts. Domain: only data and rules. No HTTP,
DB, gRPC.
2ndDependencies go inward. Application uses Domain. Infrastructure uses
Application and Domain.
3rdOne area = one module. Each area has Domain, Application, Infrastructure.

#### Layers

Domain — Data and rules only. No HTTP, DB, or frameworks. Django & .NET:
same idea (data, rules).
Application — What the app does and how we connect. No DB or HTTP here.
Django: use cases, ports. .NET: use cases, services, interfaces.
Infrastructure — Real work: DB, gRPC, HTTP, Kafka. Django: DB access, gRPC,
HTTP views, Kafka. .NET: same (repos, gRPC, API, messages).
One domain, one application, one infrastructure per area
One project. Each area (CRM, Loyalty, Bonus, Wheel, Tournaments, Campaign, Marketing) has one
domain, one application, one infrastructure. One repo, one deploy. Same rules: inner parts don’t
depend on outer; domain no HTTP/DB. Use cases in application; DB, gRPC, HTTP in infrastructure.
See Folder and layout below for structure and sample (Loyalty).
Folder and layout
One domain, one application, one infrastructure per area.

Project root:
gamification
├─ ─ crm/ ├─ ─ crm/
│ ├─ ─ domain/
│ ├─ ─ application/
│ └ ─ ─ infrastructure/
├─ ─ loyalty/
│ ├─ ─ domain/
│ ├─ ─ application/
│ └ ─ ─ infrastructure/
├─ ─ bonus/
│ ├─ ─ domain/
│ ├─ ─ application/
│ └ ─ ─ infrastructure/
├─ ─ wheel/
│ ├─ ─ domain/
│ ├─ ─ application/
│ └ ─ ─ infrastructure/
├─ ─ tournaments/
One project (e.g. repo name)
│ ├─ ─ domain/
│ ├─ ─ application/
│ └ ─ ─ infrastructure/
├─ ─ campaign
_
messaging/
│ ├─ ─ domain/
│ ├─ ─ application/
│ └ ─ ─ infrastructure/
├─ ─ marketing/
│ ├─ ─ domain/
│ ├─ ─ application/
│ └ ─ ─ infrastructure/
├─ ─ shared/ │ ├─ ─ grpc/
│ ├─ ─ kafka/
│ └ ─ ─ http/
├─ ─ config/
├─ ─ tests/
├─ ─ Dockerfile
├─ ─ docker-compose.yml
└ ─ ─ requirements.txt


### Sample — Loyalty:

loyalty/
├─ ─ domain/ Data and rules only. No HTTP, DB, gRPC.
│ ├─ ─ __init__.py
│ ├─ ─ entities.py PointWallet, PointTransaction
│ ├─ ─ value_objects.py PointAmount, ConversionRate
│ └ ─ ─ exceptions.py Domain errors (InsufficientPointsError)
├─ ─ application/ Use cases and ports. No DB or HTTP.
│ ├─ ─ __init__.py
│ ├─ ─ use_cases/
│ │ ├─ ─ __init__.py
│ │ ├─ ─ award_points.py AwardPointsUseCase
│ │ ├─ ─ redeem_points.py RedeemPointsUseCase
│ │ └ ─ ─ get_balance.py GetBalanceUseCase
│ └ ─ ─ ports.py IPointWalletRepository, etc.
└ ─ ─ infrastructure/ DB, gRPC, HTTP, Kafka
├─ ─ __init__.py
├─ ─ persistence/
│ ├─ ─ __init__.py
│ └ ─ ─ point_wallet_repository.py Django ORM repo for IPointWalletRepository
├─ ─ grpc/
│ └ ─ ─ loyalty_grpc.py gRPC handlers → use cases
└ ─ ─ http/
└ ─ ─ loyalty_views.py REST views → use cases


domain/ — Entities, value objects, exceptions. No imports from application or
infrastructure.
application/ — Use cases and ports. Use cases call domain; depend on ports,
not DB/HTTP.
infrastructure/ — Repos, gRPC, HTTP. Implement ports; call use cases.
Same layout for crm, bonus, wheel, tournaments, campaign, messaging, marketing.

### Summary
Gamification + CRM only. Auth, affiliate, big reports: other services. Notifications: notification
service (gRPC/HTTP or Kafka). Observability: Logger, Jaeger, OpenTelemetry. Clean architecture:
one domain, one application, one infrastructure per area. Same gRPC + Kafka for Django and .NET.

### Code peer review
Before merge or release.
Scope & design
Scope and domains checked.
Tech stack and formats (gRPC, Kafka) checked.
Clean architecture and layers checked.
Notification service usage checked.
Unit tests: mandatory. New and changed code has unit tests before merge.

### Technical requirements
PostgreSQL: migrations, schema, connections.
Kafka: topics, schema, producers/consumers.
Docker: image, Dockerfile, run config.
Identity (auth): gRPC, calls.
Report service: gRPC, calls (if used).
APISIX / HTTP: routes, config.
Shared .proto and schema: versions, compatibility.
Env vars, secrets (DB, Kafka, URLs).
Logger: structured logging. Jaeger: tracing config,
export. OpenTelemetry: SDK, spans, metrics.
Logging, monitoring checked.
Deployment
Deploy in Docker (must use). Image and run steps defined.
Build and deploy documented.
Env: PostgreSQL, Kafka, URLs, secrets, Jaeger/OpenTelemetry endpoint (if
used).
Health checks, ready to deploy.
Rollback steps known.