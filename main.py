"""
main.py

FastAPI webhook server for the GitHub Incident AI Platform.

Receives GitHub push webhooks and runs the orchestrator agent
against the pushed commit in the background.
"""

import hashlib
import hmac
import json

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from agents import Runner

from app.agents.orchestrator_agent import orchestrator_agent
from config import settings

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)


def verify_signature(payload_body: bytes, signature_header: str | None) -> None:
    """
    Validate the X-Hub-Signature-256 header GitHub sends with each
    webhook delivery, using GITHUB_WEBHOOK_SECRET as the shared secret.
    """

    if not settings.GITHUB_WEBHOOK_SECRET:
        return

    if not signature_header:
        raise HTTPException(status_code=401, detail="Missing X-Hub-Signature-256 header")

    expected_signature = "sha256=" + hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(),
        payload_body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=401, detail="Invalid signature")


async def analyze_commit(event_text: str) -> None:
    await Runner.run(orchestrator_agent, event_text)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.VERSION}


@app.post("/webhook/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
):
    body = await request.body()
    verify_signature(body, x_hub_signature_256)

    if x_github_event == "ping":
        return {"status": "pong"}

    if x_github_event != "push":
        return {"status": "ignored", "event": x_github_event}

    payload = json.loads(body)
    commits = payload.get("commits", [])

    if not commits:
        return {"status": "ignored", "reason": "no commits in push"}

    head_commit = payload.get("head_commit") or commits[-1]
    repository = payload.get("repository", {}).get("full_name", settings.REPOSITORY)
    branch = payload.get("ref", "").rsplit("/", 1)[-1]

    event_text = f"""
Analyze the following GitHub commit.

Repository: {repository}
Branch: {branch}
Commit ID: {head_commit.get("id")}
Author: {head_commit.get("author", {}).get("name")}

Commit Message:
{head_commit.get("message")}

Determine:
1. Severity
2. Diagnosis
3. Root Cause
"""

    background_tasks.add_task(analyze_commit, event_text)

    return {"status": "accepted", "commit_id": head_commit.get("id")}
