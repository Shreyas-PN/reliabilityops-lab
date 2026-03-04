PYTHON ?= python3
COMPOSE ?= docker compose
KIND_CLUSTER ?= reliabilityops-lab

.PHONY: help setup lint format test compose-up compose-down compose-logs compose-ps kind-up kind-down k8s-build-images k8s-load-images k8s-deploy k8s-delete k8s-status

help:
	@echo "Targets:"
	@echo "  setup         Install local Python dev dependencies"
	@echo "  lint          Run ruff lint"
	@echo "  format        Run ruff formatter"
	@echo "  test          Run pytest"
	@echo "  compose-up    Start local stack via Docker Compose"
	@echo "  compose-down  Stop local stack"
	@echo "  compose-logs  Tail compose logs"
	@echo "  compose-ps    Show compose services"
	@echo "  kind-up       Create kind cluster"
	@echo "  kind-down     Delete kind cluster"
	@echo "  k8s-build-images Build local service images for kind"
	@echo "  k8s-load-images  Load local images into kind cluster"
	@echo "  k8s-deploy    Apply Kubernetes manifests"
	@echo "  k8s-delete    Delete Kubernetes manifests"
	@echo "  k8s-status    Show pod/service status"

setup:
	$(PYTHON) -m pip install -r requirements-dev.txt

lint:
	ruff check .

format:
	ruff format .

test:
	pytest

compose-up:
	$(COMPOSE) up --build -d

compose-down:
	$(COMPOSE) down -v

compose-logs:
	$(COMPOSE) logs -f --tail=100

compose-ps:
	$(COMPOSE) ps

kind-up:
	bash scripts/kind-up.sh $(KIND_CLUSTER)

kind-down:
	kind delete cluster --name $(KIND_CLUSTER)

k8s-build-images:
	docker build -t reliabilityops-lab/api:dev services/api
	docker build -t reliabilityops-lab/worker:dev services/worker
	docker build -t reliabilityops-lab/remediator:dev services/remediator

k8s-load-images:
	kind load docker-image reliabilityops-lab/api:dev --name $(KIND_CLUSTER)
	kind load docker-image reliabilityops-lab/worker:dev --name $(KIND_CLUSTER)
	kind load docker-image reliabilityops-lab/remediator:dev --name $(KIND_CLUSTER)

k8s-deploy: k8s-build-images k8s-load-images
	kubectl apply -f observability/k8s/namespace.yaml
	kubectl apply -f observability/k8s

k8s-delete:
	kubectl delete -f observability/k8s --ignore-not-found=true

k8s-status:
	kubectl get pods,svc -n reliabilityops
