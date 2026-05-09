from fastapi import Depends, FastAPI
from pydantic import BaseModel
from daifend_core.service_gate import require_internal_service_token

app = FastAPI(title="Daifend Notification Service", version="0.2.0")


class NotifyBody(BaseModel):
    tenant_id: str
    channel: str
    payload: dict


@app.get("/health")
def health():
    return {"service": "notification-service", "status": "ok"}


@app.post(
    "/v1/notify",
    dependencies=[Depends(require_internal_service_token)],
)
def notify(body: NotifyBody):
    # Wire to SendGrid / Slack / PagerDuty in production
    return {"accepted": True, "channel": body.channel}
