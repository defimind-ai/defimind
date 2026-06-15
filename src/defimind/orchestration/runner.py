"""The runner: load config → build client → run Cleo's modes → sleep → repeat.

THIN by design. It owns the loop, the per-cycle session, retry-on-cycle-error,
and the sleep interval — nothing else. Config loading lives in `config/`, the
transport in `client/`, and which modes run in `agents/cleo`.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from defimind.agents import cleo
from defimind.client import DefiMindClient
from defimind.config import load_config


async def main(config_path: Path | None = None) -> None:
    config = load_config(config_path)
    print(cleo.intro(config))

    client = DefiMindClient(config.endpoint)
    while True:
        try:
            # One MCP session per cycle: open, run every mode, close.
            async with client.session() as conn:
                await cleo.run_modes(conn, config)
        except Exception as e:  # noqa: BLE001 — one bad cycle shouldn't kill Cleo
            print(f"\n✗ cycle error (will retry next interval): {e}")
        await asyncio.sleep(config.poll_interval_seconds)
