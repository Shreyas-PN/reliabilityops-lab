# Incident Response (Local Lab)

## Triage
1. Confirm failing service via `make compose-ps`.
2. Check logs via `make compose-logs`.
3. Verify API health endpoint.

## Mitigation
1. Restart only impacted service with `docker compose restart <service>`.
2. If queue stuck, restart worker and rabbitmq.

## Post-incident
1. Capture timeline.
2. Add action items to backlog.
