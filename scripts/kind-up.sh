#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="${1:-reliabilityops-lab}"
kind create cluster --name "${CLUSTER_NAME}" --config infra/kind/kind-config.yaml
