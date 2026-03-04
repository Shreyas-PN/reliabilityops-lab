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
   - Remediator: `http://localhost:8002/healthz`
   - RabbitMQ UI: `http://localhost:15672` (`guest/guest`)

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
