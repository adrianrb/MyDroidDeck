"""Example action bindings offered by the admin UI (``POST /admin/actions/examples``).

Loaded from ``server/actions.example.json`` so the list stays human-editable and
easy to extend; duplicates (by ``action`` key) are skipped on import.
"""

from __future__ import annotations

import json
from pathlib import Path

EXAMPLES_FILE = Path(__file__).resolve().parents[2] / "actions.example.json"


def load_examples() -> list[dict]:
    """Return the example bindings, or an empty list if the file is missing."""
    try:
        data = json.loads(EXAMPLES_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    examples = data.get("examples", [])
    return examples if isinstance(examples, list) else []