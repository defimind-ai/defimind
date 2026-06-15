"""Format a tool result + alerts into a printed human-readable block.

Isolated here on purpose: MVP-B hooks rendering and MVP-C hooks anchoring at
this layer. Keep formatting decisions in one place.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


def report_pool(pool_label: str, tool: str, payload: Any, alerts: list[str]) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    print(f"\n[{ts}] {pool_label} — {tool}")
    if isinstance(payload, (dict, list)):
        print(json.dumps(payload, indent=2, default=str))
    else:
        print(payload)
    for a in alerts:
        print(f"  ⚠ ALERT: {a}")
