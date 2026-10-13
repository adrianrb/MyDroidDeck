# MyDroidDeck — installers

Turns the `server/` component into an installable app. There are two flavors:

- **Windows** — an **Inno Setup** installer that ships a self-contained, offline
  bundle (embeddable Python + wheels): **no login**, default port **56997**, plain
  **HTTP**. It installs **per-user under your HOME** (`%USERPROFILE%\MyDroidDeck`)
  and needs **no elevation**. It opens `/admin/config` in the browser after the
  first install.
- **Linux/WSL** — a per-user shell installer (`setup/linux/install-server.sh`)
  with the same behavior: detects the environment, installs under your HOME
  (default `~/MyDroidDeck`), adds Configuração / start / stop / restart /
  readme.txt shortcuts when a GUI is present (and in the Windows Start menu under
  WSL), offers autostart at logon, and opens the Configuração page in Firefox.

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
from `server/version.txt`). The installer, its uninstaller and every Start-menu
shortcut use `app.ico`, which mirrors the Android launcher icon; regenerate it
from the app's vector with `python3 setup/windows/make-icon.py` if the icon changes.

### 3. Install

The installer is **per-user and does not request elevation**: it installs under
`%USERPROFILE%\MyDroidDeck` (you can change the folder on the wizard's location
page). It offers:

- **Iniciar no logon do Windows** — adds a hidden launcher
  (`MyDroidDeck.vbs`) to your **Startup** folder (no admin, no console window).

The **Start menu → MyDroidDeck** group gets: *Configuração do MyDroidDeck*
(starts the server and opens the page in Firefox), *Iniciar servidor*, *Parar
servidor*, *Reiniciar servidor*, *readme.txt* and *Desinstalar*. The same
operations are available from a console via `start.cmd`, `stop.cmd`,
`restart.cmd` and `status.cmd` in the install folder.

Install layout (all under your HOME):

| Path | Contents |
| --- | --- |
| `%USERPROFILE%\MyDroidDeck\server\` | server code |
| `%USERPROFILE%\MyDroidDeck\runtime\` | embedded Python |
| `%USERPROFILE%\MyDroidDeck\tools\` | `control.ps1`, `firewall.ps1` |
| `%USERPROFILE%\MyDroidDeck\*.cmd` | `start` / `stop` / `restart` / `status` scripts |
| `%USERPROFILE%\MyDroidDeck\readme.txt` | usage notes |
| `%USERPROFILE%\MyDroidDeck\data\` | `runtime.json`, `mydroiddeck.db`, `icons\` |
| `%USERPROFILE%\MyDroidDeck\logs\server.log` | server log |

On finishing, the wizard starts the server, waits until it answers and then
opens `http://127.0.0.1:56997/` in the browser (the wait avoids a first-request
404; the root redirects to the Configuração page).

**LAN access.** Since the installer is not elevated, it does **not** add a
firewall rule. To expose the server to other devices, run this **once** in an
elevated PowerShell (then turn on *Visível na rede*):

```powershell
powershell -ExecutionPolicy Bypass -File "%USERPROFILE%\MyDroidDeck\tools\firewall.ps1" -Action add
```

### Uninstall

Use *Apps & features* (or the Start-menu shortcut). The uninstaller first stops
the server (and removes the Startup entry and the Start-menu shortcuts), then
**asks whether to delete all data**. Choose *Yes* to wipe the whole install folder
(profiles, paired devices, actions, icons and logs under `data\`/`logs\`); choose
*No* (or run it silently) to keep your `data\` folder.

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
that helper the toggles are simply recorded (no error). On the Linux/WSL install the
launcher records those settings too, but the page's restart button has no Windows
helper — control the server with `bin/mydroiddeck start|stop|restart|status` instead
(also reachable from the desktop / Start-menu shortcuts).

## Linux / WSL

A per-user, self-contained shell installer (no root needed). It detects the
environment and prerequisites, installs under your HOME and, when it can,
autostarts the server and adds the shortcuts:

```bash
setup/linux/install-server.sh
# --prefix DIR   --port N   --autostart auto|systemd|xdg|profile|none
# --no-desktop   --no-open  --no-start   --install-deps   --yes
# --uninstall    --dry-run
```

What it does:

1. **Detects the environment** — distro, package manager, `python3 >= 3.10` +
   `venv`, a GUI (`$DISPLAY`/`$WAYLAND_DISPLAY` + `xdg-open`) and, under WSL, the
   Windows interop. With `--install-deps` (or a prompt) it runs the right
   `apt/dnf/pacman/apk/zypper` command through `sudo` for missing prerequisites.
2. **Installs under your HOME** — default `~/MyDroidDeck` (change with `--prefix`).
   It copies `server/` next to a fresh `venv/`, so the git clone can be removed
   afterwards.
3. **Adds shortcuts** — `.desktop` entries (Configuração / start / stop / restart /
   readme.txt) on your Desktop and in `~/.local/share/applications` on a Linux GUI;
   under WSL it also creates the same set in the Windows **Start menu**
   (`MyDroidDeck\`) plus `MyDroidDeck.lnk` on the Windows **Desktop** (launching
   `wsl.exe`).
4. **Offers autostart at logon** — `systemd --user` when available, else an XDG
   autostart entry (GUI) or a guarded block in `~/.profile` (WSL). Choose with
   `--autostart`; use `--autostart none` to skip.

Layout (default `~/MyDroidDeck`):

| Path | Contents |
| --- | --- |
| `server/` | server code (copied) |
| `venv/` | Python virtualenv |
| `bin/mydroiddeck` | server control: `start` / `stop` / `restart` / `status` / `open` / `readme` (no argument = foreground, used by systemd) |
| `bin/mydroiddeck-open` | alias of `mydroiddeck open` (start-if-needed + open the page) |
| `tools/windows-shortcut.ps1` | Windows Desktop/Start-menu shortcuts (WSL only) |
| `readme.txt` | usage notes |
| `data/` | `runtime.json`, `mydroiddeck.db`, `icons/` |
| `logs/server.log` | server log |

On finishing it starts the server and opens `http://127.0.0.1:56997/` in
**Firefox** — never the Windows default browser (override the path with
`MYDROIDDECK_WIN_BROWSER`).

`--uninstall` removes the autostart entry and the shortcuts (it then asks whether
to delete the install folder too).

Smoke tests: `setup/tests/test-install-server.sh`.

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
