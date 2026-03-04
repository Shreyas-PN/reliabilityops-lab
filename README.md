# reliabilityops-lab

A local, production-style monorepo for simulating a modern SRE/DevOps platform.
It gives recruiters and hiring teams a concrete, hands-on signal of platform engineering, observability, reliability workflows, and operational readiness.

## What This Simulates

- `api` (FastAPI) with health, readiness, metrics, and task enqueue endpoints
- `worker` that consumes RabbitMQ tasks, retries on failure, and routes exhausted messages to a DLQ
- `remediator` webhook listener service
- `postgres`, `redis`, `rabbitmq` as core dependencies
- `prometheus` + `grafana` for local observability

## Architecture Overview

- API exposes `/healthz`, `/readyz`, `/metrics`, and accepts `POST /task` into RabbitMQ.
- Worker consumes tasks from `tasks`, retries up to configured limits, sends failures to `tasks.dlq`, and writes task status to Redis keys (`task:<id>:status`).
- Remediator acts as a webhook listener for automated-action simulation.
- Prometheus scrapes API metrics and Grafana auto-provisions datasource/dashboard files from the repo.

```text
                +-----------------------+
                |       Grafana         |
                |  dashboards + panels  |
                +-----------+-----------+
                            |
                            | query
                            v
+---------+   scrape   +----+-----+     publish      +-----------+
| Browser | ---------> | Prometheus| <-------------- | API       |
+---------+  /metrics  +----------+                  | FastAPI   |
      |                                             /healthz      |
      | HTTP                                        /readyz       |
      |                                             /metrics       |
      |                                             POST /task     |
      v                                                        |
+-----------+  webhook  +-------------+                        |
| Remediator| <-------- | External    |                        v
+-----------+           | Trigger     |                  +-----+------+
                        +-------------+                  | RabbitMQ   |
                                                         | tasks/dlq  |
                                                         +-----+------+
                                                               |
                                                               | consume/retry/dlq
                                                               v
                                                         +-----+------+
                                                         | Worker     |
                                                         +-----+------+
                                                               |
                                                               | status writes
                                                               v
                                                         +-----+------+
                                                         | Redis      |
                                                         +------------+
```

## Quickstart (5 Minutes)

### Prerequisites

- Docker Desktop
- Python 3.11+
- kind
- kubectl

### Commands

```bash
make setup
make compose-up
```

### Verify URLs and Credentials

- API health: http://localhost:8000/healthz
- API readiness: http://localhost:8000/readyz
- Remediator health: http://localhost:8002/healthz
- RabbitMQ UI: http://localhost:15672 (`guest` / `guest`)
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (`admin` / `admin`)

## 2-Minute Demo

Generate traffic so Prometheus/Grafana panels populate:

```bash
for i in {1..10}; do
  curl -fsS http://localhost:8000/healthz >/dev/null
  curl -fsS http://localhost:8000/readyz >/dev/null
done
```

Send a sample task into RabbitMQ via API:

```bash
curl -fsS -X POST http://localhost:8000/task \
  -H 'Content-Type: application/json' \
  -d '{"task_id":"demo-001","payload":{"action":"rotate-token"}}'
```

Validate worker status in Redis and queue state in RabbitMQ:

```bash
docker compose exec -T redis redis-cli GET task:demo-001:status
docker compose exec -T rabbitmq rabbitmqctl list_queues name messages
```

Open Grafana and confirm the pre-provisioned dashboard appears:

```bash
open http://localhost:3000/d/reliabilityops-api/reliabilityops-api-overview
```

## Observability

### How Metrics Work

The API exposes Prometheus-compatible metrics at:

- http://localhost:8000/metrics

Prometheus scrapes `api:8000/metrics` using `observability/prometheus/prometheus.yml`.

### PromQL Examples (Metrics That Exist in This Repo)

```text
sum(rate(api_http_requests_total[5m]))
```

```text
sum(rate(api_http_requests_total{path="/readyz"}[5m]))
```

```text
histogram_quantile(0.95, sum(rate(api_http_request_duration_seconds_bucket[5m])) by (le))
```

### Grafana Provisioning (Repo Paths)

- Datasource config: `observability/grafana/provisioning/datasources/datasource.yml`
- Dashboard provider config: `observability/grafana/provisioning/dashboards/dashboards.yml`
- Dashboard JSON: `observability/grafana/dashboards/reliabilityops-api.json`

Verify provisioning loaded:

```bash
curl -u admin:admin -fsS http://localhost:3000/api/datasources
curl -u admin:admin -fsS "http://localhost:3000/api/search?query=ReliabilityOps"
```

## How To Run (Observability Only)

```bash
docker compose up --build -d
curl -s http://localhost:8000/healthz >/dev/null
curl -s http://localhost:8000/readyz >/dev/null
```

## Kubernetes (kind)

```bash
make kind-up
make k8s-deploy
make k8s-status
```

`k8s-deploy` builds service images, loads them into kind, then applies manifests.

## CI

GitHub Actions workflow runs on push/PR and executes:

- `make lint` (ruff)
- `make test` (pytest)

Workflow file:

- `.github/workflows/ci.yml`

## Troubleshooting

### Docker Not Found or Docker Desktop Not Running

```bash
docker version
docker compose version
```

If these fail, start Docker Desktop and retry `make compose-up`.

### Ports Already In Use

Required host ports: `8000`, `8002`, `3000`, `9090`, `15672`.

```bash
lsof -nP -iTCP:8000,8002,3000,9090,15672 -sTCP:LISTEN
```

Stop conflicting processes or remap ports in `docker-compose.yml`.

### Grafana Shows "No Dashboards"

Common root cause: provisioning/dashboard directories are not mounted.

Expected `docker-compose.yml` mounts for `grafana`:

```yaml
volumes:
  - ./observability/grafana/provisioning:/etc/grafana/provisioning:ro
  - ./observability/grafana/dashboards:/var/lib/grafana/dashboards:ro
```

Verify files exist in repo:

```bash
ls -la observability/grafana/provisioning/datasources
ls -la observability/grafana/provisioning/dashboards
ls -la observability/grafana/dashboards
```

Then restart stack:

```bash
docker compose down -v
docker compose up --build -d
```

## Stop and Cleanup

```bash
make compose-down
```

`make compose-down` runs `docker compose down -v`.
The `-v` flag removes named volumes (including local Postgres data) for a clean reset.

## Repo Layout

- `services/` application services
- `infra/kind/` kind cluster config
- `infra/terraform/` IaC placeholder
- `observability/` local compose + Kubernetes manifests
- `runbooks/` operational docs
- `scripts/` helper scripts
