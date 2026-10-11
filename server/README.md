# MyDroidDeck server

FastAPI backend for MyDroidDeck: stores deck profiles, serves a server-rendered
admin UI (Jinja), and dispatches button actions over REST.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Run (dev)

```bash
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Endpoints:

- `GET /health`, `GET /version` (public)
- `POST /pair` — exchange the shared pairing code for a per-device token (public)
- `GET|POST /profiles`, `GET /profiles/{id}`, `DELETE /profiles/{id}`, `POST /actions`
  — protected: send `Authorization: Bearer <token>` from `/pair`
- `GET /admin/profiles`, `GET|POST /admin/profiles/…`, `GET /admin/devices`,
  `POST /admin/devices/{id}/revoke` — server-rendered admin UI (not authenticated yet)

Config is overridable with `MYDROIDDECK_*` env vars (see `app/core/config.py`);
SQLite is used by default.

## Test

```bash
.venv/bin/pytest
```
