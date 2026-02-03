# Quick Start Guide

How to run Kafka, Jaeger, and all tools for the Gamification service.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose installed (comes with Docker Desktop)

## Starting All Services

### Option 1: Start Everything (Recommended)

```bash
# From the project root directory
docker compose up -d
```

This starts all services in detached mode:

- PostgreSQL (database)
- Redis (caching)
- Zookeeper + Kafka (event streaming)
- Schema Registry (Avro schema management)
- Jaeger (distributed tracing)
- Gamification API (HTTP/REST)
- Gamification gRPC (gRPC server)

### Option 2: Start Only Infrastructure (Without App)

If you want to run the Django app locally but use Docker for infrastructure:

```bash
# Start only infrastructure services
docker compose up -d postgres redis zookeeper kafka schema-registry jaeger

# Then run Django locally
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Option 3: Start Specific Services

```bash
# Start only Kafka and dependencies
docker compose up -d zookeeper kafka schema-registry

# Start only Jaeger
docker compose up -d jaeger

# Start only database
docker compose up -d postgres redis
```

## Service URLs and Ports


| Service               | URL                                              | Port  | Description                  |
| --------------------- | ------------------------------------------------ | ----- | ---------------------------- |
| **Gamification API**  | [http://localhost:8000](http://localhost:8000)   | 8000  | Django REST API              |
| **Gamification gRPC** | localhost:50051                                  | 50051 | gRPC server                  |
| **PostgreSQL**        | localhost:5432                                   | 5432  | Database                     |
| **Redis**             | localhost:6379                                   | 6379  | Cache                        |
| **Kafka**             | localhost:9092                                   | 9092  | Kafka broker (internal)      |
| **Kafka (external)**  | localhost:29092                                  | 29092 | Kafka broker (from host)     |
| **Schema Registry**   | [http://localhost:8081](http://localhost:8081)   | 8081  | Avro schema registry         |
| **Jaeger UI**         | [http://localhost:16686](http://localhost:16686) | 16686 | Jaeger tracing UI            |
| **Jaeger Collector**  | [http://localhost:14268](http://localhost:14268) | 14268 | Jaeger trace collector       |
| **Zookeeper**         | localhost:2181                                   | 2181  | Zookeeper (Kafka dependency) |


## Checking Service Status

```bash
# View all running containers
docker compose ps

# View logs for all services
docker compose logs -f

# View logs for specific service
docker compose logs -f kafka
docker compose logs -f jaeger
docker compose logs -f gamification-api

# Check health status
docker compose ps
```

## Accessing Services

### Jaeger UI (Tracing)

Open in browser: **[http://localhost:16686](http://localhost:16686)**

- View traces from your application
- Search by service name: `gamification`
- Filter by operation, tags, etc.

### Schema Registry UI

The Schema Registry doesn't have a built-in UI, but you can use:

```bash
# List all subjects (schemas)
curl http://localhost:8081/subjects

# Get latest version of a schema
curl http://localhost:8081/subjects/{subject-name}/versions/latest
```

### Kafka Topics

```bash
# List all topics
docker exec gamification-kafka kafka-topics --bootstrap-server localhost:9092 --list

# Create a topic manually (if needed)
docker exec gamification-kafka kafka-topics --bootstrap-server localhost:9092 \
  --create --topic audit-logs --partitions 1 --replication-factor 1

# Describe a topic
docker exec gamification-kafka kafka-topics --bootstrap-server localhost:9092 \
  --describe --topic audit-logs

# Consume messages from a topic
docker exec -it gamification-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 --topic audit-logs --from-beginning
```

### PostgreSQL Database

```bash
# Connect to database
docker exec -it gamification-postgres psql -U postgres -d gamification

# Or from host (if you have psql installed)
psql -h localhost -U postgres -d gamification
```

## Stopping Services

```bash
# Stop all services (keeps containers)
docker compose stop

# Stop and remove containers (keeps volumes/data)
docker compose down

# Stop and remove everything including volumes (⚠️ deletes data)
docker compose down -v
```

## Restarting Services

```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart kafka
docker compose restart jaeger
```

## Running Migrations

After starting PostgreSQL, run Django migrations:

```bash
# If running app in Docker
docker compose exec gamification-api python manage.py migrate

# If running app locally
python manage.py migrate
```

## Environment Variables

Create a `.env` file (copy from `.env.example`) to customize:

```bash
# Copy example
cp .env.example .env

# Edit .env with your preferred values
```

Key variables:

- `DB_PASSWORD` - PostgreSQL password
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `KAFKA_BOOTSTRAP_SERVERS` - Kafka brokers (default: localhost:9092)
- `JAEGER_ENDPOINT` - Jaeger collector URL

## Troubleshooting

### Port Already in Use

If a port is already in use:

```bash
# Find what's using the port (macOS/Linux)
lsof -i :8000
lsof -i :9092
lsof -i :16686

# Kill the process or change the port in docker compose.yml
```

### Services Not Starting

```bash
# Check logs for errors
docker compose logs kafka
docker compose logs jaeger

# Check if containers are running
docker compose ps

# Restart a specific service
docker compose restart kafka
```

### Kafka Connection Issues

```bash
# Verify Kafka is healthy
docker exec gamification-kafka kafka-topics --bootstrap-server localhost:9092 --list

# Check Kafka logs
docker compose logs kafka | tail -50
```

### Database Connection Issues

```bash
# Verify PostgreSQL is ready
docker exec gamification-postgres pg_isready -U postgres

# Check database exists
docker exec gamification-postgres psql -U postgres -l | grep gamification
```

## Development Workflow

### Typical Development Setup

1. **Start infrastructure:**
  ```bash
   docker compose up -d postgres kafka zookeeper schema-registry jaeger
  ```
2. **Run migrations:**
  ```bash
   python manage.py migrate
  ```
3. **Run Django locally (with hot-reload):**
  ```bash
   python manage.py runserver
  ```
4. **Run gRPC server locally:**
  ```bash
   python -m shared.grpc.server
  ```
5. **Access services:**
  - API: [http://localhost:8000](http://localhost:8000)
  - Jaeger: [http://localhost:16686](http://localhost:16686)
  - Kafka: localhost:9092

### Testing with All Services Running

```bash
# Start everything
docker compose up -d

# Run tests
pytest

# Check logs
docker compose logs -f gamification-api
```

## Next Steps

- See [deploy.md](deploy.md) for production deployment
- See [technical_guideline.md](technical_guideline.md) for architecture details
- See [project_index.md](project_index.md) for project structure
