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
  `POST /admin/devices/{id}/revoke`, `GET|POST /admin/actions`,
  `POST /admin/actions/{id}/delete`, `POST /admin/actions/examples`
  — server-rendered admin UI, **requires login** (see below)

Config is overridable with `MYDROIDDECK_*` env vars (see `app/core/config.py`);
SQLite is used by default.

## Test

```bash
.venv/bin/pytest
```

## Admin UI — login

As páginas HTML (`/admin/…`) exigem **login** (usuário/senha). Configure em
`server/.env` (gitignored):

```bash
MYDROIDDECK_ADMIN_USER=admin
MYDROIDDECK_ADMIN_PASSWORD=uma-senha-forte
MYDROIDDECK_ADMIN_SECRET_KEY=<aleatório estável>   # assina o cookie de sessão
# MYDROIDDECK_ADMIN_SESSION_SECONDS=43200          # validade da sessão (12h)
```

Gere o segredo com:
`python3 -c "import secrets;print(secrets.token_urlsafe(32))"`.

- A sessão é um **cookie assinado** (HMAC-SHA256, `httponly`, `samesite=lax`), sem
  store no servidor; expira conforme `MYDROIDDECK_ADMIN_SESSION_SECONDS`.
- `GET /admin/login` mostra o formulário; `POST /admin/logout` encerra a sessão.
- Visitas sem sessão válida são redirecionadas (HTTP 303) para o login.
- Se os defaults (`admin`/`admin`, segredo `change-me`) não forem trocados, o
  servidor registra um **aviso no log** ao iniciar.
- A API REST continua usando **token por dispositivo** (`Authorization: Bearer`),
  independente deste login.

## Ações → executáveis do Windows

Cada botão do deck envia uma **chave de ação** (`POST /actions` — o texto depois do
`|` em `rótulo|ação`). O servidor só executa o que o admin mapeou: em
**`/admin/actions`** cadastre `ação → executável do Windows (+ argumentos)`.

Como o servidor roda no WSL2, o programa é iniciado via **interop do WSL**
(`powershell.exe` + `Start-Process`), **destacado e sem janela de console**; o
`POST /actions` responde na hora.

| `action` (chave) | `executable` | `args` |
| --- | --- | --- |
| `obs.scene.iniciar` | `C:\Program Files\obs-studio\bin\64bit\obs64.exe` | `--startrecording` |
| `bloco.notas` | `notepad.exe` | |
| `meu.script` | `C:\scripts\setup.bat` | |

- Ação **sem binding** → resposta `{"status":"unknown"}` e **nada é executado**
  (strings arbitrárias vindas dos aparelhos ficam inertes).
- Caminhos com espaços são citados com segurança (literais do PowerShell).
- As últimas execuções aparecem em `/admin/actions` (`last_run_at` / `last_status`).
- `MYDROIDDECK_EXEC_ENGINE=dry-run` simula o lançamento (não abre programa) — usado
  pelos testes; `MYDROIDDECK_EXEC_TIMEOUT_SECONDS` limita o launcher.

### Bindings de exemplo

O botão **Importar exemplos** em `/admin/actions` (`POST /admin/actions/examples`)
carrega os exemplos de **`server/actions.example.json`**, ignorando chaves que já
existem (idempotente). Já vêm prontos: Bloco de Notas, Calculadora, Paint,
Explorador, Gerenciador de Tarefas, **kiTTY portable**
(`C:\Desenv\Util\kiTTY-PuTTY-auto-reconnect\kitty_portable-0.74.0.4.exe`) e dois
modelos (OBS Studio e um `.bat`) — ajuste os caminhos desses dois na sua máquina.

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

> ⚠️ O admin HTML (`/admin/devices`, `/admin/actions`) mostra o código de pareamento
> e permite **cadastrar executáveis que o servidor lança no Windows**. Ele **exige
> login** (`MYDROIDDECK_ADMIN_*`), mas **não usa HTTPS** — mantenha em LAN confiável
> e troque as credenciais padrão antes de expor.
