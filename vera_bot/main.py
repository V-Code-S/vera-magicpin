from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict

from bot import compose

app = FastAPI()

# in-memory store
store = {}

# ─────────────────────────────
# MODELS
# ─────────────────────────────


class ContextRequest(BaseModel):
    scope: str
    id: str
    payload: Dict


class TickRequest(BaseModel):
    category: Dict
    merchant: Dict
    trigger: Dict
    customer: Optional[Dict] = None


class ReplyRequest(BaseModel):
    message: str
    state: Dict

# ─────────────────────────────
# ENDPOINTS
# ─────────────────────────────


@app.get("/v1/healthz")
def health():
    return {"status": "ok"}


@app.get("/v1/metadata")
def metadata():
    return {
        "name": "Vera Bot",
        "version": "1.0",
        "description": "Trigger-aware engagement AI"
    }


@app.post("/v1/context")
def context(req: ContextRequest):
    store[(req.scope, req.id)] = req.payload
    return {"status": "stored"}


@app.post("/v1/tick")
def tick(req: TickRequest):
    result = compose(
        req.category,
        req.merchant,
        req.trigger,
        req.customer
    )
    return result


@app.post("/v1/reply")
def reply(req: ReplyRequest):
    msg = req.message.lower()

    if "yes" in msg:
        return {
            "action": "send",
            "body": "Great — applying it now. I’ll share preview shortly."
        }

    if "no" in msg:
        return {
            "action": "end"
        }

    return {
        "action": "send",
        "body": "Got it — want me to proceed now or schedule later?"
    }
