# AGENTS.md

## Project
**MyDroidDeck** — a "Stream Deck for Android": an Android device acts as a
programmatic macro/control deck. `app/` = Android client, `server/` = FastAPI
backend that stores profiles, serves an admin UI, and dispatches commands. Both
components build green. This is the only instruction file; no CI, pre-commit, or
`opencode.json`.

## Environment (Windows 11 host; the agent runs in WSL)
- This session is Linux/WSL; the Windows `C:` drive is mounted at `/mnt/c` and paths
  are **case-sensitive** (`/mnt/c/Desenv`, not `/mnt/c/desenv`). Repo:
  `/mnt/c/Desenv/_Projetos/IA/MyDroidDeck` (git, branch `master`).
- Windows dev tools are **not on the WSL `PATH`**; call them by absolute path.
  Windows binaries run as `.exe` via WSL interop.
  - JDK 21 → `/mnt/c/desenv/JDKs/jdk-21.0.7/bin/java.exe` (jdk-17 also present).
  - Android SDK → `C:\desenv\Android\Sdk` (platform-tools, platforms;android-34,
    build-tools;34.0.0). `JAVA_HOME`/`ANDROID_HOME` are **not** set globally.
  - `adb` → `C:\desenv\Android\Sdk\platform-tools\adb.exe`.
  - Default browser on this PC → `C:\Desenv\Util\Firefox\firefox.exe` (open URLs
    with it; the Windows installer prefers it via `tools\open-console.ps1`).
- **Build/test `app/` from Windows, not WSL**: the SDK ships Windows binaries that
  Linux `gradlew` cannot use. Use the helper (sets `JAVA_HOME`/`ANDROID_HOME`, then
  calls the wrapper):
  `cmd.exe /c 'C:\Desenv\_Projetos\IA\MyDroidDeck\app\gradlew-win.bat --no-daemon test'`
  `app/local.properties` (gitignored) sets `sdk.dir`.
- `server/` uses WSL `python3` (3.11) in `server/.venv`.
- Permissions: agents may **read all of `C:`** but may **write only inside this repo
  and `/tmp`**.

## Stack
- `app/` — native Android, Kotlin 1.9.24 + Jetpack Compose (Material 3), Compose
  compiler 1.5.14, AGP 8.5.2, Gradle 8.7, `minSdk 24`/`compileSdk 34`, Java 17.
  Retrofit + OkHttp + Gson.
- `server/` — Python 3.10+ FastAPI (`app.main:app`), server-rendered Jinja admin UI,
  SQLAlchemy 2 + SQLite, `pydantic-settings`. Python 3.10+; package `mydroiddeck-server`.

## Commands
```bash
# server (always run from server/ — see gotcha below)
cd server && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"   # setup
cd server && .venv/bin/pytest                        # all tests (addopts "-q")
cd server && .venv/bin/pytest tests/test_actions.py  # one file
cd server && .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# app — run through gradlew-win.bat (from Windows cmd.exe)
...\gradlew-win.bat --no-daemon test
...\gradlew-win.bat --no-daemon test --tests "com.mydroiddeck.app.ui.DeckStateTest"
...\gradlew-win.bat --no-daemon assembleDebug   # -> app/build/outputs/apk/debug/
```

## Gotchas
- **Run the server from `server/`.** `Settings` reads `.env` relative to the CWD and
  `sqlite:///./…` is CWD-relative; from the repo root you get a stray DB and miss
  `.env`. The deploy scripts already `cd` to `server/`.
- `app/version.txt` must match `X.Y.Z`; `app/build.gradle` **throws** (build fails) on
  any other format. `versionCode` is derived as `major*10000 + minor*100 + patch`.
- **i18n**: pt-BR is the default and every user-facing string must be externalized.
  Add each new string to **both** catalogs: server
  `server/app/i18n/locales/{pt_BR,en}.json` and Android
  `app/src/main/res/values/strings.xml` (pt-BR default) + `values-en/`. Tests assert
  on i18n keys / localized output, never literal pt-BR text.
- **Server tests are hermetic** via `server/tests/conftest.py`: it sets a throwaway
  SQLite DB, `MYDROIDDECK_EXEC_ENGINE=dry-run` (never launches real Windows
  programs), a temp icon cache, and fixed admin/pairing creds *before* settings load,
  so a developer's `.env` never changes results. Use the `client` / `admin_client` /
  `anon_client` fixtures; `dry-run` makes `/icon` return 404.
- **App tests are JVM-only** (`app/src/test/…`, JUnit); there are no instrumentation
  tests yet. `test` does not build the APK.
- `git` shows an untracked screenshot `2026-10-11 17-16-36 erro app.png` in the repo
  root — not part of the project.

## Conventions (project-owner directives)
- Versioning: **SemVer X.Y.Z, independent per component**; each `version.txt`
  (`app/version.txt`, `server/version.txt`) is that component's single source of truth
  (`versionName`/`versionCode`; server `/version` + `/health`).
- **Before every commit, bump the build number (Z in X.Y.Z)** of the component(s)
  touched, e.g. `0.4.0` → `0.4.1`. Touching both components bumps both files.
- **When the user asks for a "fork" (a variant, e.g. the no-login fork), create a
  git branch first** (e.g. `fork/no-login`) and do the work there.
- UTF-8 everywhere (source, config, data).
- Every feature ships with unit + integration tests. See `docs/TEST_PLAN.md`.
- Use sub-agents in parallel when tasks are independent.

## Layout
- `server/app/` — `api/` routers (`actions`, `admin`, `health`, `pairing`,
  `profiles`), `models/` ORM, `schemas/` Pydantic, `core/` (`security.py` device-token
  auth, `admin_auth.py` login + signed cookie, `executor.py` runs Windows executables
  via WSL interop, `icons.py` extracts real program icons, `config.py` `MYDROIDDECK_*`
  settings), `i18n/locales/*.json`, `templates/` + `static/` Jinja admin UI,
  `actions.example.json` seed bindings; tests in `server/tests/`.
- `app/src/main/java/com/mydroiddeck/app/` — `MainActivity`, `model/`, `net/`
  (`ApiClient` base URL + bearer interceptor, `TokenStore`), `ui/` (`DeckScreen`,
  `DeckIcons`, `DeckState`, `PairingScreen`, `ThemeMode`, `ui/theme/`).
  `res/values/` is pt-BR (default), `res/values-en/` English.

## Deploy (local, WSL host)
- The server runs **detached** (`setsid` + `nohup`): **Ctrl+C won't stop it**. Manage
  with `server/deploy/{start,stop,status}.sh` (PID/log in `server/deploy/`, secrets in
  gitignored `server/.env`, DB in `server/data/`). Bound to `0.0.0.0:8000` in WSL2.
- Emulator reaches the host via `10.0.2.2`. A physical device needs the Windows
  portproxy + firewall rule: run `server/deploy/lan-proxy.ps1` **elevated**. It targets
  the **current WSL2 IP** — re-run after a reboot / `wsl --shutdown` (forwarding to
  `127.0.0.1` does not work on this host). Set the app's server URL to the Windows LAN
  IP (`https://…:8000/`).
- **HTTPS/TLS**: `server/deploy/gen-cert.sh` writes a self-signed cert to
  `server/deploy/tls/` (gitignored) with SANs for `localhost`/`10.0.2.2`/host LAN IPs,
  and copies the public cert to `app/src/main/res/raw/mydroiddeck_server.pem`.
  `MYDROIDDECK_SSL_CERTFILE`/`_SSL_KEYFILE` in `server/.env` make `start.sh` serve
  HTTPS; the app trusts that cert via `network_security_config.xml`. **Re-run the
  script and rebuild the app if the LAN IP changes.**
- App install on a connected device:
  `cmd.exe /c 'C:\desenv\Android\Sdk\platform-tools\adb.exe install -r C:\Desenv\_Projetos\IA\MyDroidDeck\app\build\outputs\apk\debug\MyDroidDeck-debug.apk'`
- The app's cleartext network config stays broad for LAN dev (and trusts the dev TLS
  cert); harden before any public exposure.

## Installers (`setup/`)
- `setup/windows/MyDroidDeck.iss` (Inno Setup 6.3+; Inno 7 is at
  `C:\Desenv\Util\Inno Setup 7\ISCC.exe`) packages an **offline** bundle:
  `setup/build-offline.sh` downloads a Windows embeddable Python + wheels (via `uv`)
  into `setup/build/stage/` (gitignored); the compiled installer lands in
  `setup/build/output/`. It installs **per-user** under `%USERPROFILE%\MyDroidDeck`
  with `PrivilegesRequired=lowest` (**no elevation**); data/logs live in the install
  dir. The install runs the server through `server/launch.py`, which reads
  `data/runtime.json`.
- **No-login fork**: the Windows launcher sets `MYDROIDDECK_ADMIN_AUTH_ENABLED=false`
  so the admin pages need no session; the REST API still uses device tokens. It
  defaults to **port 56997 over HTTP** (no TLS) and binds `127.0.0.1` until the user
  enables *Visível na rede* on `/admin/config` (LAN also needs an elevated
  `tools\firewall.ps1 -Action add`, since the installer is not elevated).
- `/admin/config` (new) edits `data/runtime.json` (`visible_on_network`, `port`,
  `start_on_logon`) and links to Perfis/Ações; the Windows `tools\control.ps1`
  helper adds/removes the hidden **Startup-folder** launcher and restarts the
  server. On dev machines (no helper) the toggles are only recorded. See
  `setup/README.md`.
- `setup/linux/install-server.sh` is the Linux/macOS equivalent (venv + systemd
  `--user` unit).

## Actions, pairing, admin (behavior to preserve)
- **Auth is split**: the JSON REST API uses per-device bearer tokens from `POST /pair`
  (`MYDROIDDECK_PAIRING_CODE`, dev default `pair-dev`); the admin HTML UI uses a login
  + HMAC-signed session cookie (`MYDROIDDECK_ADMIN_USER` / `_ADMIN_PASSWORD` /
  `_ADMIN_SECRET_KEY` / `_ADMIN_SESSION_SECONDS`). Re-pairing rotates a token; admin
  revoke → 401 and the app drops pairing.
- Buttons dispatch a **key**; the server executes only keys bound in `/admin/actions`
  (`server` → `powershell.exe Start-Process`, detached, no console). Unbound keys
  return `status:"unknown"` and run nothing.
  `POST /admin/actions/examples` seeds `server/actions.example.json`;
  `POST /admin/profiles/{id}/examples` adds one button per binding (both idempotent).
- `GET /icon?action=<key>` returns the bound executable's **real icon** (PNG, cached
  in `MYDROIDDECK_ICON_CACHE_DIR`, default `./data/icons`); 404 → label only.
  Pre-warmed in a background task on binding/import/seed.

## Assets & reusable code
Free / permissively-licensed assets and open-source repos, with their licenses, are
cataloged in `docs/FREE_RESOURCES.md`. Verify the license at the source and record
attribution when adding any third-party asset or dependency.
