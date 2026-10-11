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

## Android app (unit / instrumentation)
| ID | Case | Expected |
| --- | --- | --- |
| A-01 | Deck renders N×M grid from a profile | Correct button count and labels |
| A-02 | Tap a button | Correct action dispatched to server exactly once |
| A-03 | Long-press / edit a button | Edit screen opens with current values |
| A-04 | Server unreachable | Reconnect with backoff; UI shows offline state (no crash) |
| A-05 | Reconnect after network drop | Grid state re-synced |
| A-06 | Switch app locale pt-BR ⇄ en | All visible strings update; no hardcoded text |
| A-07 | Rotate / resize | Grid reflows without losing selection |
| A-08 | Profile imported with accented labels | Labels render correctly (UTF-8) |
| A-09 | App reports its version | Matches `X.Y.Z` from the build |

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

- Transport is **REST** (decided): the app `POST`s actions to `/actions`. Device
  pairing is implemented (shared `pairing_code` → per-device bearer token, S-15…S-20);
  the admin HTML UI is not authenticated yet (open).
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
