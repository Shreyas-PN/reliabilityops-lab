# reliabilityops-lab

Local monorepo that simulates a small SRE/DevOps platform:
- `api` (FastAPI)
- `worker` (RabbitMQ consumer)
- `remediator` (webhook listener)
- `postgres`, `redis`, `rabbitmq`

## Quickstart (macOS)

1. Install prerequisites: Docker Desktop, Python 3.11+, kind, kubectl.
2. Install dev tools:
   ```bash
   make setup
   ```
3. Run local stack:
   ```bash
   make compose-up
   ```
4. Verify:
   - API: `http://localhost:8000/healthz`
   - API ready: `http://localhost:8000/readyz`
   - Remediator: `http://localhost:8002/healthz`
   - RabbitMQ UI: `http://localhost:15672` (`guest/guest`)
   - Prometheus: `http://localhost:9090`
   - Grafana: `http://localhost:3000` (`admin/admin`)

## How to run (observability)

```bash
docker compose up --build -d
curl -s http://localhost:8000/healthz > /dev/null
curl -s http://localhost:8000/readyz > /dev/null
```

URLs and credentials:
- API: `http://localhost:8000` (`/healthz`, `/readyz`, `/metrics`)
- Prometheus: `http://localhost:9090` (target `api` should be UP)
- Grafana: `http://localhost:3000` (username `admin`, password `admin`)

## Kubernetes (kind)

```bash
make kind-up
make k8s-deploy
make k8s-status
```

`k8s-deploy` builds service images and loads them into kind before applying manifests.

## Repo layout

- `services/` application services
- `infra/kind/` kind cluster config
- `infra/terraform/` IaC placeholder
- `observability/` local compose + Kubernetes manifests
- `runbooks/` operational docs
- `scripts/` helper scripts
