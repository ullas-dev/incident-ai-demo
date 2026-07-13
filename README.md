# GitHub Incident AI Platform

An AI agent that analyzes GitHub commits, determines an incident's **severity**,
**diagnosis**, and **root cause**, and logs it to a local database — triggered
automatically via a GitHub webhook on every push.

## How it works

1. GitHub sends a **push webhook** to `POST /webhook/github`, with the real
   commit details (id, author, message) already attached to the payload.
2. The orchestrator agent (OpenAI Agents SDK, `gpt-4.1`) treats that commit
   data as ground truth (it can also fetch commits itself via
   `get_latest_commit`/`get_recent_commits` if asked to check the repo
   directly, outside of a webhook event), then **always fetches the actual
   diff** via `get_commit_diff` — the commit message alone is an unreliable,
   self-reported summary, so severity/diagnosis/root cause are based on what
   the code changed, not just what the author wrote.
3. It always saves the result via the `save_incident` tool into a local
   SQLite database (`data/incident.db`).

## Project structure

```
.
├── main.py                        # FastAPI app: webhook + health endpoints
├── config.py                      # Settings, loaded from .env
├── app/
│   ├── agents/
│   │   └── orchestrator_agent.py  # Agent definition, system prompt, tool wiring
│   ├── tools/
│   │   ├── github_tool.py         # get_latest_commit / get_recent_commits / get_commit_diff (PyGithub)
│   │   └── database_tool.py       # save_incident / get_all_incidents / update_incident_status
│   └── database/
│       └── database.py            # SQLite schema + queries
└── data/
    └── incident.db                # SQLite data file (created on first run)
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in:

| Variable                | Description                                              |
| ------------------------ | --------------------------------------------------------- |
| `GITHUB_TOKEN`           | Personal access token with read access to the repo         |
| `GITHUB_REPOSITORY`      | `owner/repo` to monitor                                    |
| `GITHUB_WEBHOOK_SECRET`  | Shared secret for verifying webhook payloads (optional)    |
| `OPENAI_API_KEY`         | OpenAI API key                                             |

## Running

```bash
uvicorn main:app --port 8000
```

Point a GitHub webhook (repo Settings → Webhooks) at
`http://<host>/webhook/github` for the `push` event, with content type
`application/json`. If `GITHUB_WEBHOOK_SECRET` is set in `.env`, use the same
value as the webhook's secret so signature verification passes.

`GET /health` returns a basic liveness check.

## Notes

- `data/incident.db` and `.env` are gitignored — the database is local
  runtime state, and `.env` holds live credentials.
