# Technical Guideline

**What this is:** Standards for the Gamification & CRM service — contracts, integrations, migrations, logging, PR/review, and deployment. This document is the **standard** for the service; follow it unless explicitly overridden.

**In short:**

- **One source:** All gRPC definitions (protos) and event schemas (Avro) live in the `convex-contracts` repo.
- **One version:** We use the same version number (SemVer, e.g. `v1.2.0`) for both .NET (NuGet) and Django (pip) packages.
- **Align with:** Identity, Payment, AuditReport, and Scheduler use the same patterns.

---

## Table of contents

*Table format: **§** = section number (— = unnumbered); **Section** = link to heading.*

| § | Section |
|---|---------|
| — | [Who builds what](#who-builds-what) |
| 1 | [Source of truth](#1-source-of-truth) |
| 2 | [Release (CI)](#2-release-ci) |
| 3 | [.NET: consume](#3-net-consume) |
| 4 | [Django: consume](#4-django-consume) |
| 5 | [Avro (Kafka / Redpanda)](#5-avro-kafka--redpanda) |
| 6 | [Audit: stream to audit service](#6-audit-stream-to-audit-service) |
| 7 | [Django migrations](#7-django-migrations) |
| 8 | [Scheduler (cron jobs)](#8-scheduler-cron-jobs-integration) |
| 9 | [Structured logging](#9-structured-logging) |
| 10 | [PR and code review](#10-pr-and-code-review) |
| 11 | [ID and enum standards](#11-id-and-enum-standards) |
| 12 | [After each deployment](#12-after-each-deployment) |
| 13 | [Final review (started project)](#13-final-review-started-project) |
| — | [Other considerations](#other-considerations) · [Summary](#summary) · [Project review: Gamification](project_review.md) |

---

## Who builds what

- **convex-contracts** (separate repo): **builds and publishes** the shared packages (NuGet for .NET, pip for Django). Only this repo produces new contract versions.
- **Gamification, Identity, etc.:** **only consume** — they add the package and use it. They do not publish contracts.
- Developers maintain both the `convex-contracts` repo and the service repos that use it.

---

## Recommended approach

*Table format: **Area** = topic; **Recommended** = preferred option; **Fallback** = alternative if recommended not used.*

| Area | Recommended | Fallback |
|------|-------------|----------|
| **gRPC (protos)** | Publish from convex-contracts as NuGet + pip | — |
| **Avro (Kafka/Redpanda event schemas)** | Use a Schema Registry (e.g. Confluent); publish from convex-contracts on release | Ship `.avsc` files inside NuGet + pip packages |

---

## 1. Source of truth

**Where everything lives:** The `convex-contracts` repo holds gRPC definitions (protos) and Avro event schemas. One release (e.g. tag `v1.2.0`) produces the same version for both NuGet and pip.

```
convex-contracts/
├── protos/          # gRPC
│   ├── bonus/
│   ├── identity/
│   └── ...
├── schemas/         # Kafka Avro (.avsc)
│   ├── bonus/
│   ├── identity/
│   └── ...
└── CHANGELOG.md
```

---

## 2. Release (CI)

**When we release a new version** (e.g. by creating a tag `v1.2.0` in convex-contracts), CI should:

1. **NuGet:** Build the package from protos and push to GitLab Package Registry (NuGet).
2. **pip:** Build the Python package from the same protos and push to GitLab PyPI (or your private PyPI).
3. **(Optional) Avro:** Publish `.avsc` schemas to the Schema Registry so producers/consumers can resolve by ID and version.

**Trigger:** Run the release pipeline on tag push (e.g. `v*`) or manually from `main` with a version input. Use the same version string for NuGet and pip (e.g. `1.2.0` without the `v` prefix in package metadata if your tooling expects it).

**Example (NuGet):**

```bash
dotnet pack -c Release -o ./nupkgs
dotnet nuget push ./nupkgs/*.nupkg --source "GitLab" --api-key $CI_JOB_TOKEN
```

**Example (pip):** Use a build script or `setup.py`/`pyproject.toml` that compiles protos and builds a wheel; then `twine upload` to your GitLab PyPI index (or `pip install` from a private index URL). Ensure the package name and version match the guideline (e.g. `convex-grpc-contracts==1.2.0`).

---

## 3. .NET: consume

**How .NET services use the shared contracts:**

1. **Add the GitLab NuGet source** in `nuget.config` (solution or repo root). Example:

   ```xml
   <packageSources>
     <add key="GitLab" value="https://gitlab.com/api/v4/projects/<PROJECT_ID>/packages/nuget/index.json" />
   </packageSources>
   ```

2. **Authentication:** Use a token (e.g. CI `CI_JOB_TOKEN` or a deploy token) with `read_package_registry` permission. In CI, pass it via `--api-key` or via NuGet config; locally, use `dotnet nuget add source` with the key or store credentials in the config.

3. **Reference the package** in your `.csproj` (pin the version; avoid floating unless you have a reason):

**Package reference:**

```xml
<PackageReference Include="Convex.Grpc.Contracts" Version="1.2.0" />
```

After restore, use the generated C# types and gRPC clients from the package namespace (e.g. `Convex.Grpc.Contracts.Bonus`) in your service code.

---

## 4. Django: consume

**How Django (e.g. Gamification) uses the shared contracts:**

1. **Add the package** to `requirements.txt` and pin the version so builds are reproducible:

**requirements.txt:**

```text
convex-grpc-contracts==1.2.0
```

2. **In code,** import the generated gRPC stubs and use them in your servicers and clients:

```python
from convex_grpc_contracts import bonus_pb2_grpc, identity_pb2_grpc
# Use bonus_pb2 for message types, bonus_pb2_grpc for servicer base classes and stubs
```

3. **Private registry:** If the package is hosted on GitLab PyPI or another private index, configure pip before install:
   - **Environment:** Set `PIP_INDEX_URL` and `PIP_EXTRA_INDEX_URL` (or `PIP_INDEX_URL` plus a token in the URL) in CI and local env.
   - **pip.conf / pip.ini:** Add an `[global]` or `[install]` section with `extra-index-url` and optionally `trusted-host`.
   - **CI:** Use a CI variable (e.g. `CI_JOB_TOKEN` or a deploy token) in the index URL so `pip install -r requirements.txt` can pull the package.

---

## 5. Avro (Kafka / Redpanda)

**What Avro is:** The format we use for event/message schemas on Kafka (or Redpanda). Same rules apply for both. Schemas define the shape of messages so producers and consumers stay compatible.

- **Recommended — Schema Registry:** Store `.avsc` files in convex-contracts under `schemas/` (e.g. `schemas/bonus/FreebetCreated.avsc`). On release, register or upload each schema to the Schema Registry (e.g. Confluent or Redpanda built-in). Producers and consumers then resolve schemas by subject/ID and use the same `SCHEMA_REGISTRY_URL` (and auth if private). This gives central versioning and compatibility checks.
- **Fallback — no registry:** If you don’t use a registry, bundle the `.avsc` files inside the NuGet and pip packages (e.g. in a `schemas/` folder in the package). Services load the files from the package at runtime and use them for serialization/deserialization. Document which package version maps to which schema version.

**Example `.avsc`:**

```json
{
  "type": "record",
  "name": "FreebetCreated",
  "namespace": "convex.bonus.v1",
  "fields": [
    { "name": "public_id", "type": "string" },
    { "name": "tenant_id", "type": "string" },
    { "name": "occurred_at", "type": "long", "logicalType": "timestamp-millis" }
  ]
}
```

---

## 6. Audit: stream to audit service

**Why:** So all important actions and errors are stored in one place (AuditReport) and can be searched.

Gamification (and other services) send audit and exception logs to **AuditReport** via Kafka. AuditReport consumes these and stores them (e.g. in ClickHouse, ScyllaDB, or Elasticsearch).

**When to publish:**
- **audit-logs:** After important actions (e.g. freebet created, status updated, user action). One message per logical event.
- **exception-logs:** When an exception or error occurs that you want to track centrally (e.g. unhandled exception, validation failure, or business-rule violation). Include enough context (service, tenant, request/trace id) for debugging.

**Message shape:** Use the same fields as other services (e.g. from `Convex.AuditReport.Contracts` or shared Avro): at least Id, ServiceName, TenantId, Action, EntityType, EntityId, CreatedAt; add Payload or Message for details. Gamification (Django) can produce JSON or Avro; if Avro, use the shared schema from convex-contracts so AuditReport can deserialize.

*Table format: **Item** = topic; **Detail** = what to do or use.*

| Item | Detail |
|------|--------|
| **Topics** | `audit-logs`, `exception-logs` |
| **Other services** | Identity, Payment, Localization, SportBook use `Convex.AuditReport.Contracts`; use the **same message shape**. |
| **Gamification (Django)** | Publish to `audit-logs` after important actions; to `exception-logs` on exceptions. Match AuditReport.Contracts fields (Id, ServiceName, TenantId, Action, EntityType, EntityId, CreatedAt, etc.). |
| **Config** | `KAFKA_BOOTSTRAP_SERVERS`, `AUDIT_LOGS_TOPIC=audit-logs`, `EXCEPTION_LOGS_TOPIC=exception-logs` |

---

## 7. Django migrations

**Why:** To avoid production incidents from risky schema changes. We lint migrations and follow a clear process.

**Tool:** **django-migration-linter** — checks each migration for risky operations (e.g. adding a non-nullable column without a default, dropping a column, renaming without a dedicated migration, or large table changes that can lock the table). Fix or acknowledge any reported issues before merge. Run it in CI.

*Table format: **Action** = step; **Command** = what to run.*

| Action | Command |
|--------|--------|
| Install | `pip install django-migration-linter` |
| Run | `python manage.py lintmigrations` (add to CI) |
| Optional | `django-linear-migrations` — one linear migration chain per app |

**Practices:**

- **One logical change per migration.** For example: one migration adds a column, another adds an index. Do not edit a migration that has already been applied; add a new migration to fix or adjust.
- **Run migrate in a separate step** before starting the app. In the deploy pipeline: run `python manage.py migrate --no-input` (or equivalent) in a dedicated step; only then start or update the app process. This avoids running migrations from multiple instances and makes failures easier to see.
- **Deploy order:** backup DB (optional but recommended for major releases) → run migrations → deploy new code → smoke/health checks.
- **CI:** Run `makemigrations --check --dry-run` so uncommitted model changes fail the build; run `lintmigrations` so risky migrations are caught. Keep all migration files in version control and never delete applied migrations.

---

## 8. Scheduler (cron jobs) integration

**Why:** One central Scheduler runs cron jobs and calls each service when a job is due. Services only need to implement “run this job and report back.”

Same pattern as Identity and Payment: register jobs with the Scheduler; implement **JobExecutionService** (receive ExecuteJob, run the task, report status).

**Gamification (Django):** Your service receives an ExecuteJob request (via gRPC or HTTP) containing a job name (and optional payload). Look up the handler for that job name, run the use case (e.g. “expiring freebets notification”), then call the Scheduler’s ReportJobCompleted (with optional result) or ReportJobFailed (with error message). Do this explicitly so the Scheduler can update job state and retry or alert if needed.

*Table format: **Item** = topic; **Detail** = description or config.*

| Item | Detail |
|------|--------|
| **Flow** | 1) Register jobs (CreateJob: target_service=gamification, target_endpoint). 2) Scheduler calls target when due. 3) Target runs task and reports status (ReportJobProcessing / Completed / Failed). |
| **Config** | `SCHEDULER_SERVICE_URL`; use same scheduler protos from convex-contracts. |

**Clean code:** Put the job dispatcher (factory) in the **Application** layer (e.g. `bonus/src/Application/jobs/`). It maps `job_name` (string from the request) to the right use case or callable (e.g. `expiring-freebets-notification` → `GetExpiringCasinoFreeBetsUseCase` plus notification sending). The Presentation layer (gRPC servicer or HTTP view) only: receives the request, parses job name, calls the factory to get the handler, runs it, then calls ReportJobCompleted or ReportJobFailed. No job logic in Presentation.

---

## 9. Structured logging

**Why:** So we can search, filter, and correlate logs across services (e.g. by `request_id` or `trace_id`). Other services use **Serilog** with a fixed structure; Django must output logs in the same shape.

**Format:** One JSON object per log line. Use the same field names across all services.

*Table format: **Field** = log key; **Type** = value type; **Description** = when to use.*

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO 8601 |
| `level` | string | `debug`, `info`, `warning`, `error` |
| `event` or `message` | string | Short description |
| `trace_id` | string | Optional; Jaeger/OpenTelemetry |
| `request_id` | string | Optional; per-request |
| `tenant_id` | string | Optional |
| `service` | string | Optional; e.g. `gamification` |
| *(extra)* | * | Any other key-value fields |

**Log level:** Configurable per environment via `LOG_LEVEL`. Read it in Django settings (e.g. `os.environ.get('LOG_LEVEL', 'INFO')`) and set the root logger or your app logger level accordingly (e.g. `logging.getLogger().setLevel(getattr(logging, LOG_LEVEL))`). Do not hardcode log level in code.

**Implementation (Django):** Use a JSON formatter so every log record is one JSON object. Options: (1) **structlog** — configure `structlog` with a JSON renderer and use it for application logs; (2) **custom logging.Formatter** — subclass `Formatter`, format the record into a dict (timestamp, level, event/message, trace_id, request_id, tenant_id, service, extras), then `json.dumps` and return. Attach the formatter to the handler used by your app logger. In middleware or at request entry, set `request_id` (and optionally `trace_id`, `tenant_id`) on the record or in a context so all logs for that request carry the same ids.

*Table format: **Environment** = deployment context; **Example** = suggested `LOG_LEVEL` value.*

| Environment | Example |
|-------------|---------|
| Production | `LOG_LEVEL=info` or `LOG_LEVEL=warning` |
| QA | `LOG_LEVEL=info` or `LOG_LEVEL=debug` |
| Development | `LOG_LEVEL=debug` |

**Sample log lines:**

```json
{"timestamp":"2026-02-02T12:00:00.000Z","level":"info","event":"freebet_created","tenant_id":"t1","freebet_id":"abc-123","service":"gamification"}
{"timestamp":"2026-02-02T12:00:01.000Z","level":"warning","event":"validation_failed","tenant_id":"t1","field":"name","error":"too short","request_id":"req-456"}
{"timestamp":"2026-02-02T12:00:02.000Z","level":"error","event":"job_failed","job_id":"j1","job_name":"expiring-freebets-notification","trace_id":"trace-789","service":"gamification"}
```

---

## 10. PR and code review

**Why:** To keep quality high and catch mistakes before they reach production. All changes go through a PR and at least one review. PRs that do not meet the standards below are not merged.

*Table format: **Check** = what to verify; **Requirement** = must be satisfied for merge.*

| Check | Requirement |
|-------|-------------|
| **Review** | At least one approval; scope and design checked. |
| **Unit tests** | Mandatory for new and changed code before merge. |
| **Clean architecture** | Domain: no HTTP/DB/gRPC; Application: no DB/HTTP; dependencies inward. |
| **Tech stack** | gRPC, Kafka, shared .proto/schema checked. |
| **Migrations** | `makemigrations --check --dry-run` and `lintmigrations` pass in CI. |
| **Lint / format** | Linter and formatter pass (e.g. ruff, black). |
| **Structured logging** | Follow §9; do not log PII (personally identifiable information). |
| **Secrets** | No secrets in code; use env or config. |

**Max PR turnaround:** Every PR must be reviewed and either merged or closed within **24 hours**. Assign a reviewer when opening the PR; reviewers should prioritise and respond same day.

**Linters and tools:** Use at least **ruff** for linting and formatting (or flake8 + isort + black). Optional: mypy (static types), django-migration-linter (migration checks). In CI, run: `ruff check .`, `ruff format --check .` (or `black --check .`), `pytest`, and `python manage.py lintmigrations` (and `makemigrations --check --dry-run`). Fail the pipeline if any of these fail.

**Pre-commit / pre-push:** Add a `.pre-commit-config.yaml` (or use pre-push hooks) that runs the same lint and format commands (e.g. ruff, ruff-format) and optionally pytest. Run `pre-commit install` so hooks run on commit or push. This catches issues before CI; CI should still run the same checks so that PRs from forks or without hooks are still validated.

---

## 11. ID and enum standards

**Why:** So we use internal IDs only inside the DB and never expose them; external systems and APIs see only stable, opaque IDs. Enums stay consistent between code and database.

*Table format: **Rule** = category; **Detail** = what to do.*

| Rule | Detail |
|------|--------|
| **Primary key** | Use an internal `id` (e.g. BigAutoField / auto-increment) as the primary key. All foreign keys between tables reference this `id`. Never expose `id` in public APIs or event payloads. |
| **Public ID** | For any entity that is exposed via APIs or to other systems, add a **public_id** (GUID/UUID). Generate it once on creation (e.g. `uuid.uuid4()`). External references, API request/response bodies, and cross-service messages use **public_id** only, never the internal `id`. This keeps internal DB details hidden and allows refactoring of primary keys. |
| **Enums in table** | Domain enums (e.g. status, currency, type) are stored as a column in the table (e.g. CharField with choices). The values in code (e.g. Python enum or string constants) and the DB column values must match exactly so that reads/writes are consistent. Use the same string in API responses if you expose the enum. |

---

## 12. After each deployment

**Why:** So everyone knows what is in production, how it was deployed, and how to roll back if needed. After every deployment, keep **main** (or the release branch) updated with this documentation.

*Table format: **What** = item to document; **Where / how** = file or practice.*

| What | Where / how |
|------|-------------|
| **Changelog / release notes** | Update `CHANGELOG.md` with version, date, and a short list of changes (features, fixes, breaking changes). Example: `## 1.2.0 (2026-02-02) - Added expiring freebets job; fixed public_id type in entity.` |
| **Deploy steps** | Document in `docs/deploy.md` or README: order of steps (e.g. backup → migrate → deploy → health check), which env vars are required, how to run migrations, and how to verify the deployment. |
| **What was deployed** | Tag the commit (e.g. `v1.2.0`) and attach release notes describing what the tag contains. In CI/CD, deploy from the tag or from a release artefact so what’s in production is traceable. |
| **Config / env** | List new or changed environment variables, config files, or secrets (names and purpose; never put secret values in the doc). Note any defaults and which environments they apply to. |
| **Rollback** | Document how to roll back: e.g. “Redeploy previous image tag `v1.1.0`” and “If this release had migrations, run reverse migrations or restore DB from backup.” Include who to contact and any ordering (e.g. roll back app before rolling back DB). |

**Rule:** Main (and tagged releases) must have enough detail so that someone can understand what is in production, how it was deployed, and how to roll back without relying on tribal knowledge.

---

## 13. Final review (started project)

**Why:** A started project (or phase) is only considered done after a **final review**. Nothing is signed off until review comments are resolved.

**When:** Do a final review before release or at the end of a phase (e.g. end of sprint or milestone).

**When is the review final?**

- The review is **final** only when there are **no open review comments** that block sign-off (or the team explicitly agrees that remaining comments are non-blocking and records that in the PR or ticket).
- **If there are review comments:** for each comment, either (1) **fix** — make the change and push; (2) **agree** — reply that you’ve applied the suggestion or agree with the feedback; (3) **discuss** — reply with a question or alternative and agree on a resolution. Then request re-review. Repeat until every comment is resolved or explicitly accepted as out of scope / won’t fix. Only then is the review final and the work can be signed off.

**Rule:** Do not treat a review as final or close the project/phase while blocking review comments are still open. If a comment is left as “non-blocking” or “nit”, the author and reviewer should agree that it doesn’t block sign-off.

**See also:** [Project review: Gamification](project_review.md) — review of the current codebase against this guideline (strengths, gaps, recommendations, final-review checklist).

---

## Other considerations

- **Compatibility:** Do not remove or renumber proto or Avro fields. If you must break compatibility (e.g. remove a field or change type), bump the MAJOR version and coordinate the upgrade across all consumers and producers. Document the breaking change in the release notes.
- **Secrets:** Keep GitLab, NuGet, pip tokens, Schema Registry URL, and any API keys in environment variables or CI/CD secrets — never in code or in committed config files. Use a secrets manager or CI masked variables for production.
- **CHANGELOG:** In convex-contracts, maintain a CHANGELOG (or release notes) that describes what changed in each release: new RPCs, new message fields, new Avro schemas, and any breaking or deprecated items.
- **Deprecation:** When you want to remove a field or RPC, mark it as deprecated first (in comments, release notes, or proto/schema metadata) and give consumers at least one release cycle to migrate. Remove it only in a later MAJOR version.
- **Schema Registry:** Use the same registry URL (and auth if it’s private) for all producers and consumers. Set it via e.g. `SCHEMA_REGISTRY_URL` and, if needed, `SCHEMA_REGISTRY_USERNAME` / `SCHEMA_REGISTRY_PASSWORD` (or equivalent). Document in deploy/config docs.

---

## Summary

**Contracts (one repo, one version):**

*Table format: **Area** = aspect; **.NET** / **Django** = stack-specific value.*

| Area | .NET | Django |
|------|------|--------|
| **Package** | NuGet `Convex.Grpc.Contracts` | pip `convex-grpc-contracts` |
| **Registry** | GitLab (NuGet) | GitLab PyPI or private |
| **Version** | Same (e.g. 1.2.0) | Same |

**Rest of the standards:**

- **Avro:** Use Schema Registry, or bundle `.avsc` in the packages.
- **Audit:** Send to Kafka topics `audit-logs` and `exception-logs`; match the message shape other services use.
- **Scheduler:** Same contract as Identity/Payment; implement ExecuteJob and report status.
- **Logging:** Structured JSON; same field names; log level configurable per environment.
- **PR:** At least one review; tests and lint required; resolve within 24 hours.
- **DB:** Internal `id` for relations; `public_id` for anything exposed; enums stored in the table.
- **After deploy:** Update main with changelog, deploy steps, and rollback instructions.
- **Final review:** For a started project or phase, do a final review before sign-off; resolve all review comments (or agree as non-blocking) before considering it final.
