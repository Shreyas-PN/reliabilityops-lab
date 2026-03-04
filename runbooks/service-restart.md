# Service Restart

## Docker Compose
```bash
docker compose restart api worker remediator
```

## Kubernetes
```bash
kubectl rollout restart deploy/api deploy/worker deploy/remediator -n reliabilityops
```
