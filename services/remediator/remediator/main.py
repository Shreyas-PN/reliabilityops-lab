from fastapi import FastAPI

app = FastAPI(title="reliabilityops-remediator")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "remediator"}


@app.post("/webhook")
def webhook(payload: dict) -> dict[str, str]:
    incident_id = payload.get("incident_id", "unknown")
    return {"status": "accepted", "incident_id": str(incident_id)}
