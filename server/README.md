# MyDroidDeck server

FastAPI backend for MyDroidDeck: stores deck profiles and (later) dispatches
commands over a WebSocket.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Run (dev)

```bash
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Endpoints: `GET /health`, `GET /version`, `GET|POST /profiles`,
`WS /ws/deck?token=dev-token`. Config is overridable with `MYDROIDDECK_*` env vars
(see `app/core/config.py`); SQLite is used by default.

## Test

```bash
.venv/bin/pytest
```
