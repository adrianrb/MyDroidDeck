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

## Deploy (neste host — WSL, sem systemd/Docker)

O servidor roda como um **processo destacado do terminal**: `setsid` + `nohup`,
então **Ctrl+C no seu shell não o derruba** (o request anterior de "ignorar Ctrl+C"
é satisfeito por isso). Segredos ficam em `.env` (gitignored; veja `.env.example`).

```bash
deploy/start.sh    # sobe em 0.0.0.0:8000 destacado; log em deploy/server.log
deploy/status.sh   # processo ativo? /health responde?
deploy/stop.sh     # para o processo registrado
```

### Acesso a partir de outros aparelhos (LAN)

O servidor escuta em `0.0.0.0` **dentro do WSL2**. O emulador Android alcança o
host via `10.0.2.2` (localhost forwarding automático). Para um aparelho físico na
LAN, é preciso rotear a porta no Windows (uma única vez, como **admin**):

```bat
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=127.0.0.1
netsh advfirewall firewall add rule name="MyDroidDeck 8000" dir=in action=allow protocol=TCP localport=8000
```

No app (tela de pareamento), informe `http://<ip-lan-do-windows>:8000/`
(ex.: `http://192.168.100.7:8000/`) e o código de pareamento.

> ⚠️ O admin HTML (`/admin/devices`) mostra o código de pareamento e **não tem
> autenticação** — não exponha na internet pública enquanto isso não for resolvido.
