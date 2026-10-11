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
| S-06 | Invalid payload (missing field) | 400, validation errors listed | ⬜ planned |
| S-07 | WebSocket client connects with a bad token | Closed with an auth error | ✅ `test_ws.py` |
| S-08 | Authenticated client dispatches an action | Command acknowledged | ✅ `test_ws.py` |
| S-09 | Locale negotiation | pt-BR default; `Accept-Language: en` returns English | ✅ `test_health.py`, `test_profiles.py` |
| S-10 | Duplicate profile name | 409 conflict | ✅ `test_profiles.py` |

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
| E-02 | Create profile on app → run on server | Action executes on the host |
| E-03 | Pair with a revoked token | Rejected with a clear message |
| E-04 | Two devices, one profile | Both see updates without clobbering |

## Non-functional
| ID | Case | Expected |
| --- | --- | --- |
| N-01 | Source/config/data files | Saved/loaded as UTF-8 |
| N-02 | Version bumps | `app` and `server` versions stay consistent per release |
| N-03 | i18n completeness | No missing keys in any shipped locale (fail build on gap) |
| N-04 | License attribution | Third-party assets/deps recorded (`docs/FREE_RESOURCES.md`) |

## Notes
- Define auth model (token format, expiry) before S-07/E-01/E-03.
- Decide REST vs WebSocket before S-08/A-02 so the tests target the real transport.
