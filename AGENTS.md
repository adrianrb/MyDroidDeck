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
- Versioning: **X.Y.Z** (semantic versioning) for both `app/` and `server/`.
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
  `schemas/` Pydantic, `core/security.py` token auth + `api/pairing.py`,
  `templates/` + `static/` Jinja admin UI, `i18n/locales/*.json` catalogs);
  pytest in `server/tests/`. Use the `server/.venv` virtualenv
  (`./.venv/bin/pytest`). Dev pairing code: `pair-dev`
  (`MYDROIDDECK_PAIRING_CODE`).
- `app/` — Android Gradle project (Kotlin + Compose). Sources in
  `app/src/main/java/com/mydroiddeck/app/` (`ui/` screens, `ui/theme/`, `model/`,
  `net/`); `res/values/` is pt-BR (default), `res/values-en/` English. Run
  `gradlew-win.bat test` (or `./gradlew test` on Windows).

## Open decisions
- `server/`: the admin HTML UI is **not authenticated yet** — device tokens protect
  only the JSON REST API (`/profiles`, `/actions`); pairing uses a shared
  `pairing_code` + per-device tokens.

## Assets & reusable code
Free / permissively-licensed assets and open-source repos, with their licenses, are
cataloged in `docs/FREE_RESOURCES.md`. Verify the license at the source and record
attribution when adding any third-party asset or dependency.
