# Test Plan (pre-implementation)

Planned test cases for the MVP. Keep this file in sync with what actually ships.

**Status:** the server cases marked ✅ are implemented in `server/tests/` and pass
with `server/.venv/bin/pytest`. Server tests use **pytest**; Android tests use
**JUnit** (unit) and **AndroidX Test / Espresso** (instrumentation).

## Conventions
- Every test asserts on behavior, not implementation details.
- All string assertions use i18n resource keys, never literal pt-BR text, so the
  suite also passes when the locale is switched.
- Cover the UTF-8 boundary (accents, emoji) at every serialization seam.

## Server (unit / integration)
| ID | Case | Expected | Status |
| --- | --- | --- | --- |
| S-01 | `GET /health` | 200 + `{status:"ok",version:"X.Y.Z"}` | ✅ `test_health.py` |
| S-02 | Version is SemVer | `version` matches `^\d+\.\d+\.\d+` | ✅ `test_health.py` |
| S-03 | Create/read/delete a profile | Persisted and returned intact (UTF-8 round-trip) | ✅ `test_profiles.py` |
| S-04 | Create a button with a non-Latin label | Same bytes after save/load (UTF-8) | ✅ `test_profiles.py` |
| S-05 | Unknown profile id | 404 with a stable error shape | ✅ `test_profiles.py` |
| S-06 | Invalid payload (missing field) | 422, validation errors listed | ✅ `test_actions.py` (actions) |
| S-07 | Dispatch an action over REST (`POST /actions`) | 200 + `{status,action,detail?,executed_at?}` | ✅ `test_actions.py` |
| S-08 | Dispatch without an `action` | 422 validation error | ✅ `test_actions.py` |
| S-09 | Locale negotiation | pt-BR default; `Accept-Language: en` returns English | ✅ `test_health.py`, `test_profiles.py` |
| S-10 | Duplicate profile name | 409 conflict | ✅ `test_profiles.py` |
| S-11 | Admin lists profiles (Jinja) | 200 HTML containing the profile name | ✅ `test_admin.py` |
| S-12 | Admin creates a profile via HTML form | 303 redirect; profile persisted | ✅ `test_admin.py` |
| S-13 | Admin form rejects a duplicate name | 409 with a localized message | ✅ `test_admin.py` |
| S-14 | Admin UI localized | pt-BR default; `Accept-Language: en` English | ✅ `test_admin.py` |
| S-15 | Pair with the correct code | 200 + token + device id | ✅ `test_pairing.py` |
| S-16 | Pair with a wrong code | 401, localized message | ✅ `test_pairing.py` |
| S-17 | Re-pairing rotates the token | Old token 401, new token works | ✅ `test_pairing.py` |
| S-18 | Protected REST without a token | 401 for `/profiles` and `/actions` | ✅ `test_pairing.py` |
| S-19 | Revoked device token | 401 after admin revoke (covers E-03) | ✅ `test_pairing.py` |
| S-20 | Admin lists and revokes devices | Devices page shows paired device; revoke works | ✅ `test_admin.py` |
| S-21 | Dispatch a configured action | Runs its Windows binding; records `last_run_at`/`last_status` | ✅ `test_actions.py` |
| S-22 | Dispatch an unconfigured action | 200 `status:"unknown"`; nothing is executed | ✅ `test_actions.py` |
| S-23 | Admin manages action bindings | Create via form (303), duplicate 409, delete | ✅ `test_admin.py` |
| S-24 | Admin pages require login | Anonymous → 303 redirect to `/admin/login` | ✅ `test_admin.py` |
| S-25 | Admin login/logout | Bad creds 401 + localized; login grants session; logout revokes | ✅ `test_admin.py` |
| S-26 | Tampered/expired session cookie | Rejected → 303 redirect | ✅ `test_admin.py` |
| S-27 | Import example bindings | 303; keys added once (idempotent); valid seeds | ✅ `test_admin.py`, `test_actions.py` |
| S-28 | TLS configuration | `tls_enabled` needs both paths; `gen-cert.sh` yields an ssl-loadable cert with the expected SANs | ✅ `test_config.py` |
| S-29 | Fill a profile with the standard actions | 303; one button per binding, idempotent, own buttons kept, sequential indexes | ✅ `test_profiles.py` |
| S-30 | Button icons (`GET /icon?action=`) | Serves the extracted PNG; 404 for unknown action/no icon; device auth required; extracts from a real Windows executable and from a Store-app alias (live — skipped without a Windows host); the shell's *jumbo* icon is preferred (≥48px, crisp on the deck) with the 32px `ExtractAssociatedIcon` as fallback; cache is stable per executable | ✅ `test_icons.py` |
| S-31 | Runtime settings (`/admin/config`) | Values persist to `data/runtime.json`; invalid port → 400; no-login mode opens the admin (login redirects to config) | ✅ `test_runtime_config.py`, `test_admin_config.py` |

## Android app (unit / instrumentation)
| ID | Case | Expected | Status |
| --- | --- | --- | --- |
| A-01 | Deck renders N×M grid from a profile | Correct button count and labels |
| A-02 | Tap a button | Correct action dispatched to server exactly once |
| A-03 | Long-press / edit a button | Edit screen opens with current values |
| A-04 | Server unreachable | UI shows the error state + retry (no crash) | ✅ device check |
| A-05 | Reconnect after network drop | Grid state re-synced | ✅ device check (retry loads the deck) |
| A-06 | Switch app locale pt-BR ⇄ en | All visible strings update; no hardcoded text |
| A-07 | Rotate / resize | Grid reflows without losing selection | ✅ device check |
| A-08 | Profile imported with accented labels | Labels render correctly (UTF-8) |
| A-09 | App reports its version | Matches `X.Y.Z` from the build |
| A-10 | Dispatch outcome mapping | `ok`/`unknown`/`failed`/`timeout` → Enviado / não configurada / Falha | ✅ `DeckStateTest.kt` |
| A-11 | Dark mode choice | system/light/dark resolution + persisted name (unknown → system); the whole window background + system-bar icons follow the choice (Compose `Surface`, not the framework theme) | ✅ `ThemeModeTest.kt` + device check |
| A-12 | Button icons | Deck draws the icon from `/icon` (real app icon, `FilterQuality.High`) — the snapshot read happens in the button's own scope, so a late-arriving icon repaints it; actions without an icon fall back to a label monogram badge; each action is fetched once | ✅ `DeckIconCacheTest.kt` + device check |
| A-15 | 3D "glass" deck buttons | Keys paint a top→bottom glass gradient, a lighter border + top sheen, a drop shadow and a press scale/haptic; palette follows the active (light/dark) scheme | ✅ device check |
| A-13 | Server URL normalization | Trim, assume `http://` without a scheme, single trailing slash; blanks/spaces rejected | ✅ `ServerUrlTest.kt` |
| A-14 | Change server after pairing | Server dialog (from the deck header or the error state) persists the URL, rebuilds the client and reloads; a different server 401s → re-pair | ✅ device check |

## End-to-end
| ID | Case | Expected |
| --- | --- | --- |
| E-01 | Pair device (scan/enter token) | Device authorized; deck loads |
| E-02 | Create profile on app → run on server | Action executes on the host (server side: configured Windows executables via WSL interop; `test_actions.py`) |
| E-03 | Pair with a revoked token | Rejected with a clear message |
| E-04 | Two devices, one profile | Both see updates without clobbering |

## Non-functional
| ID | Case | Expected |
| --- | --- | --- |
| N-01 | Source/config/data files | Saved/loaded as UTF-8 |
| N-02 | Version bumps | Each component reads its own `version.txt` (SemVer X.Y.Z): server `/version`, app `versionName` |
| N-03 | i18n completeness | No missing keys in any shipped locale (fail build on gap) |
| N-04 | License attribution | Third-party assets/deps recorded (`docs/FREE_RESOURCES.md`) |
| N-05 | Linux/WSL installer smoke test | Valid syntax, `--help`, `--dry-run` creates nothing, invalid port/option rejected, opens only Firefox, launcher exposes start/stop/restart/status/readme, shortcuts for config/start/stop/restart/readme, readme.txt shipped | ✅ `setup/tests/test-install-server.sh` |

- Transport is **REST** (decided): the app `POST`s actions to `/actions`. Device
  pairing is implemented (shared `pairing_code` → per-device bearer token, S-15…S-20);
  the admin HTML UI is authenticated with a login + signed session cookie
  (S-24…S-26).
- The admin UI is server-rendered **Jinja** (decided); its tests assert on localized
  HTML output (S-11…S-14, S-20).
- E-01 (pair device) is implemented via the pairing code; E-03 (revoked token) is
  covered by S-19.
- Action execution runs **Windows executables** from the WSL host
  (`app/core/executor.py`: `powershell.exe Start-Process`); only admin-configured
  bindings execute, arbitrary keys are inert (S-21…S-23). Tests use
  `MYDROIDDECK_EXEC_ENGINE=dry-run`.
- Versions are versioned **separately**: `server/version.txt` and `app/version.txt`
  are each component's single source of truth (N-02).
- The **Linux/WSL installer** (`setup/linux/install-server.sh`) detects the
  environment and prerequisites, installs per-user under `~/MyDroidDeck`, adds
  Configuração / start / stop / restart / readme.txt shortcuts (desktop and, under
  WSL, the Windows Start menu) and offers autostart; the installed
  `bin/mydroiddeck` exposes `start|stop|restart|status|open|readme` and opens the
  Configuração page in the owner's **Firefox** — never the Windows default browser
  (N-05).
- Admin example bindings live in `server/actions.example.json` and are imported from
  the UI (S-27).
- TLS uses a self-signed dev certificate generated by `server/deploy/gen-cert.sh` and
  trusted by the app; the settings flag and the certificate are covered by S-28.
- Buttons draw the **real icon of the bound program**: the server extracts it from the
  Windows executable (`app/core/icons.py`) and serves it at `GET /icon?action=`; the
  cache lives outside the tree (`MYDROIDDECK_ICON_CACHE_DIR`) so tests stay hermetic
  (S-30).
- A profile can be populated with the standard actions from the admin UI, one button
  per registered binding (S-29).
- The installers (`setup/`) run the server through `server/launch.py`, which reads
  the mutable `data/runtime.json` (network visibility, port, logon) edited on
  `/admin/config`; the Windows fork disables the admin login
  (`MYDROIDDECK_ADMIN_AUTH_ENABLED=false`) and defaults to port 56997 over HTTP
  (S-31).

## Device verification (manual, physical device `0084173849`)

Run with app **0.4.0** against server **0.4.0** (HTTPS), driving the app through `adb`
(taps by text via `uiautomator dump`) and inspecting the Windows host with `tasklist`.

| Check | Result |
| --- | --- |
| Standard actions, one by one (tap → status → Windows process → closed after ~10 s) | `bloco.notas`→Notepad ✅, `calc`→Calculator ✅, `gerenciador.tarefas`→Taskmgr ✅ (elevated: not closable via adb), `kitty`→kiTTY ✅, `explorer`→new window ✅ (closed via COM), `paint`→Paint ✅, `obs.gravar`→"Falha ao enviar" ✅ (OBS not installed), `script.exemplo`→"Falha ao enviar" ✅ (`C:\scripts\exemplo.bat` missing) |
| Button icons | 6 of the 8 actions serve a real PNG (`GET /icon` → 200); the 2 without are exactly the missing programs (404 → label only) |
| Monkey (seeds 1, 42, 987654 × 400 events, throttle 150 ms) | 1200 events, **0 crashes / 0 ANR**, app pid stable; 29 real dispatches (random taps do launch programs) |
| Rotation (landscape ⇄ portrait) | Deck re-renders, same state, 0 crashes |
| Server unreachable → restart | Error state + "Tentar de novo"; retry loads the deck (A-04/A-05) |
| Revoked token (401) | App clears the token and returns to pairing; re-pairing in the UI restores the deck (E-03) |
| 10 rapid taps on one button | 10 dispatches, 0 crashes, last status correct |
