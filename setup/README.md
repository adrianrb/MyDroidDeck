# MyDroidDeck — installers

Turns the `server/` component into an installable app. There are two flavors:

- **Windows** — an **Inno Setup** installer that ships a self-contained, offline
  bundle (embeddable Python + wheels): **no login**, default port **56997**, plain
  **HTTP**. It installs **per-user under your HOME** (`%USERPROFILE%\MyDroidDeck`)
  and needs **no elevation**. It opens `/admin/config` in the browser after the
  first install.
- **Linux/macOS** — a shell installer (`setup/linux/install-server.sh`) with the
  same behavior.

> ⚠️ **Security.** The no-login fork leaves the admin pages open, and the admin UI
> registers Windows programs the server will execute. By default the server binds
> to `127.0.0.1` (this PC only). Only enable **Visível na rede** on a network you
> trust; anyone who can reach the port then controls the host programs. The REST
> API keeps its per-device bearer tokens either way.

## Windows

### 1. Build the offline bundle (on WSL/Linux)

```bash
setup/build-offline.sh                 # add --clean to start over
```

It downloads the Windows **embeddable Python** and the server's **Windows wheels**
and writes the staging tree to `setup/build/stage/`. Wheel resolution uses
[`uv`](https://docs.astral.sh/uv/) (installed into `setup/build/tools-venv` if not
on `PATH`) because plain `pip` resolves environment markers for the build host.

Options: `--python 3.12.7`, `--clean`, `--no-deps-install`.

### 2. Compile the installer (on Windows)

Requires **Inno Setup 6.3+** (Inno Setup 7 works). On this machine the compiler is
at `C:\Desenv\Util\Inno Setup 7\ISCC.exe`:

```bat
"C:\Desenv\Util\Inno Setup 7\ISCC.exe" setup\windows\MyDroidDeck.iss
```

The result is `setup\build\output\MyDroidDeck-<version>-setup.exe` (version comes
from `server/version.txt`).

### 3. Install

The installer is **per-user and does not request elevation**: it installs under
`%USERPROFILE%\MyDroidDeck` (you can change the folder on the wizard's location
page). It offers:

- **Iniciar no logon do Windows** — adds a hidden launcher
  (`MyDroidDeck.vbs`) to your **Startup** folder (no admin, no console window).

Install layout (all under your HOME):

| Path | Contents |
| --- | --- |
| `%USERPROFILE%\MyDroidDeck\server\` | server code |
| `%USERPROFILE%\MyDroidDeck\runtime\` | embedded Python |
| `%USERPROFILE%\MyDroidDeck\tools\` | `control.ps1`, `firewall.ps1` |
| `%USERPROFILE%\MyDroidDeck\data\` | `runtime.json`, `mydroiddeck.db`, `icons\` |
| `%USERPROFILE%\MyDroidDeck\logs\server.log` | server log |

On finishing, the wizard starts the server, waits ~5 s for it to boot and then
opens `http://127.0.0.1:56997/` in the browser (the wait avoids a first-request
404; the root redirects to the Configuração page).

**LAN access.** Since the installer is not elevated, it does **not** add a
firewall rule. To expose the server to other devices, run this **once** in an
elevated PowerShell (then turn on *Visível na rede*):

```powershell
powershell -ExecutionPolicy Bypass -File "%USERPROFILE%\MyDroidDeck\tools\firewall.ps1" -Action add
```

### Uninstall

Use *Apps & features* (or the Start-menu shortcut). Uninstall removes the Startup
entry; your `data\` folder is kept.

## The Configuração page (`/admin/config`)

The single entry point after install:

| Option | Effect |
| --- | --- |
| **Visível na rede** | Bind `0.0.0.0` (LAN) instead of `127.0.0.1` (this PC). Also needs the firewall rule above. |
| **Porta** | TCP port (default 56997). |
| **Iniciar no logon** | Add/remove the Startup-folder launcher (via `tools\control.ps1`). |
| **Perfis** / **Ações** | Shortcuts to the profile and action managers. |
| **Reiniciar servidor** | Restarts the server so network/port changes take effect. |

Network and port changes only apply **after a restart** (the page says so and has a
restart button). The settings live in `data/runtime.json`, read by
`server/launch.py`:

```json
{ "visible_on_network": false, "port": 56997, "start_on_logon": false }
```

On the Windows install the launcher sets `MYDROIDDECK_ADMIN_AUTH_ENABLED=false`
and points `MYDROIDDECK_CONTROL_HELPER` at `tools\control.ps1`; on machines without
that helper the toggles are simply recorded (no error).

## Linux / macOS

```bash
setup/linux/install-server.sh                 # --prefix DIR --port N --no-service
```

Creates a virtualenv under `~/.local/share/mydroiddeck/venv`, installs `server/`,
writes the `~/.local/share/mydroiddeck/bin/mydroiddeck` launcher, seeds
`data/runtime.json`, and (with systemd) installs the `mydroiddeck.service` user
unit. It then opens `http://127.0.0.1:56997/admin/config`.

## Troubleshooting

- **Server doesn't start / browser can't connect.** Read
  `%USERPROFILE%\MyDroidDeck\logs\server.log` (the launcher appends stderr there).
- **`ModuleNotFoundError: No module named 'app'`.** The embeddable Python ships a
  `._pth` file, which suppresses the usual "script directory goes on `sys.path`"
  behavior. `server/launch.py` adds its own directory to `sys.path` explicitly, so
  rebuild/upgrade if you see this on an old install.
- **Changed the port/visibility but nothing happened.** Network and port changes
  need a restart (use the button on `/admin/config`).

## Manual run (no installer)

The runtime settings also drive a hand-started server:

```bash
cd server
.venv/bin/python launch.py    # honors data/runtime.json
```
