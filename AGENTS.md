# AGENTS.md

## Project
**MyDroidDeck** — a "Stream Deck for Android": an Android device acts as a
programmatic macro/control deck. `app/` = Android client, `server/` = backend that
stores profiles and dispatches commands. Scaffolds for both exist and build green.

## Environment (Windows 11 host; the agent runs in WSL)
- This session is Linux/WSL; the Windows `C:` drive is mounted at `/mnt/c` and paths
  are **case-sensitive** (`/mnt/c/Desenv`, not `/mnt/c/desenv`). The repo is at
  `/mnt/c/Desenv/_Projetos/IA/MyDroidDeck` (a git repo, branch `master`).
- `C:\desenv` holds portable Windows dev tools that are **not on the WSL `PATH`**.
  Call them by absolute path; Windows binaries run as `.exe` (WSL interop works):
  - JDK 21 → `/mnt/c/desenv/JDKs/jdk-21.0.7/bin/java.exe` (also jdk-17.0.x, jdk-8, 13)
  - Maven 3.6.3 → `/mnt/c/desenv/Maven/apache-maven-3.6.3/bin/mvn`
  - Node 20.11.1 / npm → `/mnt/c/desenv/NodeJS/node-v20.11.1-win-x64/`
    (`node` is not resolvable in WSL — use `node.exe` or the absolute path; `npm` works)
  - Flutter → `/mnt/c/desenv/flutter`; Git portable → `/mnt/c/desenv/Git`
  - Python 3.10 (Windows) → `/mnt/c/desenv/Python/3.10.4-x64/python.exe`; WSL also
    has `python3` 3.11 (used for the `server/` virtualenv)
- The Android SDK is installed at `C:\desenv\Android\Sdk` (platform-tools,
  platforms;android-34, build-tools;34.0.0). `JAVA_HOME` is **not** set globally.
- **Build `app/` from Windows, not WSL:** the SDK ships Windows binaries that Linux
  `gradlew` cannot use. Use the helper, which sets `JAVA_HOME`/`ANDROID_HOME` and
  calls the Gradle wrapper (Gradle 8.7, already downloaded):
  `cmd.exe /c 'C:\Desenv\_Projetos\IA\MyDroidDeck\app\gradlew-win.bat --no-daemon test'`
  `app/local.properties` (gitignored) sets `sdk.dir` to the SDK.
- `adb` is at `C:\desenv\Android\Sdk\platform-tools\adb.exe` (older copies under
  `/mnt/c/desenv/Util/scrcpy/`).
- Permissions: agents may **read all of `C:`** and may **write only inside this repo
  and `/tmp`**.

## Conventions (project-owner directives)
- Versioning: **X.Y.Z** (semantic versioning), **independent per component** — each
  has its own `version.txt` (`app/version.txt`, `server/version.txt`) as the single
  source of truth (`versionName`/`versionCode` on the app; `/version` + `/health` on
  the server).
- Encoding: **UTF-8** everywhere (source, config, data).
- Language: **pt-BR is the default**, and both app and server must support
  internationalization — externalize all strings into resource bundles, never
  hardcode user-facing text.
- Tests: every feature ships with tests (unit + integration). See `docs/TEST_PLAN.md`.
- Use sub-agents in parallel when tasks are independent.

## Intended stack
- `app/` — native Android in **Kotlin + Jetpack Compose** (Material 3). Kotlin
  1.9.24, Compose compiler 1.5.14, AGP 8.5.2, `minSdk 24`.
- `server/` — **Python + FastAPI** (owner decision): REST transport between app and
  server, server-rendered **Jinja** admin UI, SQLAlchemy + SQLite for dev.

## Layout
- `server/` — FastAPI app in `server/app/` (`api/` routers, `models/` ORM,
  `schemas/` Pydantic, `core/security.py` device-token auth + `api/pairing.py`,
  `core/admin_auth.py` admin login/session, `core/executor.py` launches configured
  **Windows executables** for dispatched actions via WSL interop, `templates/` +
  `static/` Jinja admin UI incl. `/admin/actions`, `i18n/locales/*.json` catalogs,
  `actions.example.json` seed bindings); pytest in `server/tests/`.
  Use the `server/.venv` virtualenv (`./.venv/bin/pytest`). Dev pairing code:
  `pair-dev` (`MYDROIDDECK_PAIRING_CODE`). Version: `server/version.txt`.
- `app/` — Android Gradle project (Kotlin + Compose). Sources in
  `app/src/main/java/com/mydroiddeck/app/` (`ui/` screens, `ui/theme/`, `model/`,
  `net/`); `res/values/` is pt-BR (default), `res/values-en/` English. Run
  `gradlew-win.bat test` (or `./gradlew test` on Windows). Version:
  `app/version.txt` (feeds `versionName`/`versionCode`).

## Deploy (local, WSL host)
- The FastAPI server runs detached from the terminal (`setsid`): **Ctrl+C doesn't
  stop it**. Manage it with `server/deploy/{start,stop,status}.sh` (log+PID in
  `server/deploy/`, secrets in gitignored `server/.env`, DB in `server/data/`).
- It is bound to `0.0.0.0:8000` inside WSL2. Emulator reaches it via `10.0.2.2`;
  a physical device needs the Windows portproxy + firewall rule — run
  `server/deploy/lan-proxy.ps1` (elevated PowerShell), which targets the **current
  WSL2 IP** (re-run after a reboot / `wsl --shutdown`; forwarding to `127.0.0.1`
  does not work on this host) — and the app's server URL set to the Windows LAN IP
  (now `https://`).
- **HTTPS/TLS**: `server/deploy/gen-cert.sh` writes a self-signed cert to
  `server/deploy/tls/` (gitignored) with SANs for `localhost`/`10.0.2.2`/the host
  LAN IPs, and copies the public cert to `app/src/main/res/raw/mydroiddeck_server.pem`.
  `MYDROIDDECK_SSL_CERTFILE`/`_SSL_KEYFILE` in `server/.env` make `start.sh` serve
  HTTPS; the app trusts that cert via `network_security_config.xml`. Re-run the
  script and rebuild the app if the LAN IP changes.
- App install on a connected device (Windows paths needed for `adb.exe`):
  `cmd.exe /c 'C:\desenv\Android\Sdk\platform-tools\adb.exe install -r C:\Desenv\_Projetos\IA\MyDroidDeck\app\build\outputs\apk\debug\MyDroidDeck-debug.apk'`
- The app's cleartext network config stays broad for LAN dev (and trusts the dev
  TLS cert); harden before any public exposure.
- Button actions execute **Windows executables** configured in `/admin/actions`
  (server → `powershell.exe Start-Process`, WSL interop). Only configured bindings
  run; anything else returns `status:"unknown"`. `POST /admin/actions/examples`
  seeds the example set from `server/actions.example.json`.
- The admin HTML UI requires login (`MYDROIDDECK_ADMIN_USER` / `_ADMIN_PASSWORD` /
  `_ADMIN_SECRET_KEY` in `server/.env`); the session is a signed cookie with
  `MYDROIDDECK_ADMIN_SESSION_SECONDS` lifetime.

## Open decisions
- `server/` auth: the admin HTML UI uses a **login + signed session cookie**
  (`MYDROIDDECK_ADMIN_*`); the JSON REST API uses per-device bearer tokens. TLS is
  available (self-signed dev cert, `MYDROIDDECK_SSL_*`), so enable it on any network
  you don't fully trust and set non-default admin credentials in `server/.env`.

## Assets & reusable code
Free / permissively-licensed assets and open-source repos, with their licenses, are
cataloged in `docs/FREE_RESOURCES.md`. Verify the license at the source and record
attribution when adding any third-party asset or dependency.
