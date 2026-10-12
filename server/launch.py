"""Start the server with the settings saved in ``data/runtime.json``.

The installed Windows launcher (``run-server.cmd``) and the Linux installer call
this instead of ``uvicorn`` directly, so the network visibility/port edited on the
``/admin/config`` page take effect on the next restart.
"""

from __future__ import annotations

import sys
from pathlib import Path

# The Windows "embedded" Python ships a ._pth file, which suppresses the usual
# "script directory goes on sys.path" behavior — add it explicitly so the bundled
# ``app`` package is importable. (Harmless with a normal interpreter.)
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.runtime_config import load_runtime_config  # noqa: E402


def main() -> None:
    config = load_runtime_config()

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=config.host,
        port=config.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
