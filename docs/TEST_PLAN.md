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
| S-32 | Update a profile (`PUT /profiles/{id}`) | Replaces name/locale and the full button list in the given order (re-indexed); 409 on taken name; 404 on missing id | ✅ `test_profiles.py` |
| S-33 | Admin edits a profile | Edit page prefilled; form POST persists name/locale/buttons; a button can be moved up/down inside the profile (deck order) | ✅ `test_admin.py` |
| S-34 | Admin edits an action + chooses its icon | Edit page prefilled; rebinding `executable`/`args` persists; a custom icon path (`.png`/`.ico`/`.exe`) is served by `GET /icon` and by the admin preview — empty means the executable's own icon; missing custom icon → 404 | ✅ `test_admin.py`, `test_icons.py` |
| S-35 | Admin reorders actions | ↑/↓ move endpoints persist a dense `sort_order`; the actions list and the "fill profile" order follow it | ✅ `test_admin.py` |
| S-36 | Professional admin UI (sidebar/cards) | Base layout restyled; pages render with the new chrome; mobile narrow layout; login is a standalone centered card | ✅ rendered by `test_admin.py` |
| S-37 | Pick a path with the native Windows dialog (`/admin/pick-file`) | The action form offers "Browse…" next to the executable and the custom-icon fields; the endpoint returns the chosen path as JSON (`{"path": null}` when dismissed or without a Windows host) and sits behind the admin guard; the filter covers `.exe`/`.bat` and `.ico`/`.png`; the form previews the picked icon live via `/admin/icon-preview` | ✅ `test_admin.py`, `test_file_picker.py` |
| S-38 | Rebinding an action refreshes its icon | Changing the executable (or the custom icon) drops the cached PNG so the deck/`GET /icon` re-extracts the new one; saving with no such change keeps the cache untouched | ✅ `test_admin.py` |
| S-39 | Show the server version in the admin | The sidebar footer shows `Versão do servidor: X.Y.Z` (from `server/version.txt`) on every admin page, localized (`Server version` in en) | ✅ `test_admin.py` |
| S-40 | Installer + shortcuts use the app's icon | `MyDroidDeck.iss` sets `SetupIconFile`/`UninstallDisplayIcon` and every Start-menu shortcut to `app.ico`, regenerated from the Android launcher vector by `setup/windows/make-icon.py` | ✅ ISCC compile (manual check on Windows) |
| S-41 | Uninstaller offers to delete all data | The interactive uninstaller first stops the server, then asks whether to wipe the whole install folder (profiles, paired devices, actions, icons, logs); "No"/silent keeps `data\` | ✅ ISCC compile (manual check on Windows) |
| S-42 | Pair a new device by QR (`Dispositivos → Parear novo`) | The devices page links to `/admin/devices/pair`, which shows a QR whose payload is `mydroiddeck://pair?url=<server>&code=<code>` plus the URL and the code as text; a loopback host is swapped for the machine's LAN address (warning when it stays local); `/admin/devices/pair.png` serves that PNG, `segno`-encoded and decoded back by an independent reader; both routes need the admin session and are localized | ✅ `test_pairing_qr.py` |
| S-43 | Connectivity card on `/admin/config` | Lists the transports: **USB** shows the `adb reverse tcp:<port> tcp:<port>` command and the `http://127.0.0.1:<port>/` address the app must use, **Wi-Fi** points at *Visível na rede* + the firewall rule and **Bluetooth** says it is pending; the **Conectar por USB** button posts `/admin/config/usb` (303 → `?usb=1`) and calls the host helper with `-Action usb-connect`, confirming when it comes back; the card is localized (pt-BR/en) | ✅ `test_admin_config.py` + device check (`adb reverse` registered from the phone) |
| S-44 | Installer offers the connectivity choices | The wizard's *Conectividade* group is a multiple choice: **USB** (default on; adds the *Conectar por USB* shortcut and runs `adb reverse` at the end of the install), **Wi-Fi/rede local** (default on → `visible_on_network: true` in `data\runtime.json`) and **Bluetooth** (listed but disabled: no RFCOMM transport yet); the finish page adds the firewall reminder when Wi-Fi is chosen | ✅ ISCC compile + silent install check on Windows (`visible_on_network` true/false per task) |
| S-45 | Linux/WSL installer offers the same choices | `--connectivity usb,wifi|usb|wifi|none` (asks when interactive, USB+Wi-Fi preselected); Wi-Fi seeds `visible_on_network: true`; USB adds the *Conectar por USB* `.desktop`/Windows shortcut running `bin/mydroiddeck usb` (`adb reverse tcp:<port> tcp:<port>`, `usb-off` removes it); an invalid value aborts | ✅ `setup/tests/test-install-server.sh` (19 ok) + real install into a temp prefix (`visible_on_network` true/false) |
| S-46 | *Backup* card on `/admin/config` (Exportar… / Importar…) | **Exportar…** (`GET /admin/config/export`) downloads `mydroiddeck-<timestamp>.json` — UTF-8, `Content-Disposition: attachment` — with `format`/`format_version`, the runtime settings, the action bindings (in admin order) and the profiles with their buttons (deck order); **Importar…** (`POST /admin/config/import`, file field) upserts by profile name / action key, restores the settings into `runtime.json` and redirects 303 to `?imported=1&profiles=N&actions=M[&settings=1]` with a localized summary; a wipe → import restores the exported file byte-for-byte (modulo timestamps); files that are not a MyDroidDeck bundle (bad JSON, other `format`, other `format_version`, blank names) are rejected 400 with a localized message and change nothing; both routes require the admin session | ✅ `test_admin_backup.py` (12) |

## Android app (unit / instrumentation)
| ID | Case | Expected | Status |
| --- | --- | --- | --- |
| A-01 | Deck renders N×M grid from a profile | Correct button count and labels |
| A-02 | Tap a button | Correct action dispatched to server exactly once |
| A-03 | Long-press / edit a button | Edit screen opens with current values |
| A-04 | Server unreachable | UI shows the error state + retry (no crash) | ✅ device check |
| A-05 | Reconnect after network drop | Grid state re-synced | ✅ device check (retry loads the deck) |
| A-06 | Switch app locale pt-BR ⇄ en | All visible strings update; no hardcoded text |
| A-07 | Rotate / resize | Grid reflows **and keeps the user's profile**: the deck remembers the chosen profile *by name* (`profileIndexByName`), so the recreated screen (rotation) or a reload resolves it back — falling back to the first profile only when it was renamed/removed server-side | ✅ `DeckStateTest.kt` + device check |
| A-08 | Profile imported with accented labels | Labels render correctly (UTF-8) |
| A-09 | App reports its version | Matches `X.Y.Z` from the build (`BuildConfig.VERSION_NAME`, shown in Configuração > Sobre) | ✅ device check |
| A-10 | Dispatch outcome mapping | `ok`/`unknown`/`failed`/`timeout` → Enviado / não configurada / Falha | ✅ `DeckStateTest.kt` |
| A-11 | Dark mode choice | system/light/dark resolution + persisted name (unknown → system); the whole window background + system-bar icons follow the choice (Compose `Surface`, not the framework theme) | ✅ `ThemeModeTest.kt` + device check |
| A-12 | Button icons | Deck draws the icon from `/icon` (real app icon, `FilterQuality.High`) — the snapshot read happens in the button's own scope, so a late-arriving icon repaints it; actions without an icon fall back to a label monogram badge; each action is fetched once | ✅ `DeckIconCacheTest.kt` + device check |
| A-15 | 3D "glass" deck buttons | Keys paint a top→bottom glass gradient, a lighter border + top sheen, a drop shadow and a press scale/haptic; palette follows the active (light/dark) scheme | ✅ device check |
| A-13 | Server URL normalization | Trim, assume `http://` without a scheme, single trailing slash; blanks/spaces rejected | ✅ `ServerUrlTest.kt` |
| A-14 | Change server after pairing | Server dialog (from the deck header or the error state) persists the URL, rebuilds the client and reloads; a different server 401s → re-pair | ✅ device check |
| A-16 | Reorder buttons in the deck | "Organizar" mode rings a picked button; tapping a second button swaps them and PUTs the full profile back (`/profiles/{id}`), re-indexing 0..n-1; out-of-range/identical swaps are no-ops; failures revert the optimistic order | ✅ `DeckStateTest.kt`, `DtosTest.kt` |
| A-17 | Configuração > Sobre (app + server versions) | The header "Configuração" menu groups the theme choices, the server address and **Sobre**; the dialog shows `BuildConfig.VERSION_NAME` and, fetched live via `GET /version`, the server version (unavailable → a clear message); the server URL is shown too | ✅ `DtosTest.kt` + device check |
| A-18 | Configuração > Atualizar (refresh everything) | The menu's **Atualizar** item drops the icon cache and re-fetches the profiles from the server (back to the loading state), resetting arrange mode and the last status; the icon cache bumps a generation counter so every button re-fetches even when its action key did not change | ✅ `DeckIconCacheTest.kt` + device check |
| A-19 | First run scans the pairing QR | With no token the pairing screen opens the camera by itself (and a **Ler QR code** button re-opens it); a `mydroiddeck://pair?url=…&code=…` payload fills the server URL (normalized) and the code, other QR codes show a clear error and leave the fields alone; entering them by hand still works | ✅ `PairingQrTest.kt` + device check |
| A-20 | Icons survive a refresh | **Atualizar** clears the icon cache and reloads the profiles, which cancels the fetches still in flight (the deck is swapped for the loading state). A cancelled fetch releases its "already asked" slot, so the next composition re-requests the icon instead of leaving every button on its monogram; a fetch that *finished* (icon or 404) is still cached for the screen; switching servers also drops the icons | ✅ `DeckIconCacheTest.kt` + device check |
| A-21 | Deck keys keep the portrait size in landscape | The keys are sized by the screen's **stable portrait width** (`smallestScreenWidthDp`): portrait keeps 4 columns and landscape keeps that same key size, fitting extra columns as the insets-safe width allows instead of stretching or shrinking the 4 keys; never fewer than 4 columns | ✅ `DeckStateTest.kt` + device check |
| A-22 | Deck clears the system bars (edge-to-edge) | The activity is edge-to-edge, so the deck and the pairing form are padded by `WindowInsets.safeDrawing`: the deck header stays below the status bar/camera cutout and the status line above the navigation bar, and the grid is clear of the side cutout in landscape (its column count comes from that same insets-safe width) | ✅ device check |

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
Note (0.5.5+): Compose ignores the 0-duration `adb shell input tap`; press a target with
`adb shell input swipe X Y X Y 150` (a 150 ms press at the same point) instead. From
0.5.6 the deck content is inset from the system bars, so the header buttons sit *below*
the status bar/cutout and their taps land (before, the top of those buttons was owned by
SystemUI and swallowed the touch).

| Check | Result |
| --- | --- |
| Standard actions, one by one (tap → status → Windows process → closed after ~10 s) | `bloco.notas`→Notepad ✅, `calc`→Calculator ✅, `gerenciador.tarefas`→Taskmgr ✅ (elevated: not closable via adb), `kitty`→kiTTY ✅, `explorer`→new window ✅ (closed via COM), `paint`→Paint ✅, `obs.gravar`→"Falha ao enviar" ✅ (OBS not installed), `script.exemplo`→"Falha ao enviar" ✅ (`C:\scripts\exemplo.bat` missing) |
| Button icons | 6 of the 8 actions serve a real PNG (`GET /icon` → 200); the 2 without are exactly the missing programs (404 → label only) |
| Monkey (seeds 1, 42, 987654 × 400 events, throttle 150 ms) | 1200 events, **0 crashes / 0 ANR**, app pid stable; 29 real dispatches (random taps do launch programs) |
| Rotation (landscape ⇄ portrait) | Deck re-renders, 0 crashes, and **keeps the profile the user picked** (A-07): with *Utilidades* selected, portrait → landscape → portrait stayed on *Utilidades* (only the last status line resets, expected). Keys keep their size (A-21): measured via `uiautomator dump` on this 1080x2400 / 400dpi device — portrait 4 columns of 255 px (key 229 px), landscape 8 columns of 264 px (key 238 px, +4% rounding) |
| System bars / camera cutout (A-22) | Edge-to-edge + `WindowInsets.safeDrawing`: portrait the header sits at y 130..230 (status bar/cutout = 0..110) and *Pronto.* ends at y 2260 (nav bar starts at 2280); landscape (cutout 0..110 on the left, nav bar at x 2280) the grid runs x 130..2260. Tapping a header arrow just under the bar works in both — y 140 portrait, y 110 landscape — and each tap switched the profile |
| Server unreachable → restart | Error state + "Tentar de novo"; retry loads the deck (A-04/A-05) |
| Revoked token (401) | App clears the token and returns to pairing; re-pairing in the UI restores the deck (E-03) |
| 10 rapid taps on one button | 10 dispatches, 0 crashes, last status correct |
