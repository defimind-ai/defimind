"""Cleo — the LP analyst persona.

This is where "it's always Cleo, in modes" lives: her voice (the intro line) and
the binding of which mode(s) run. At MVP-A that's thin — one mode, monitoring —
but new modes get added here, not scattered across the runner.

Cleo watches and reports. She does NOT trade, rebalance, or move funds.
"""

from __future__ import annotations

from defimind.client import DefiMindClient
from defimind.config import Config
from defimind.modes import monitoring


def intro(config: Config) -> str:
    """Cleo's opening line for a monitoring run."""
    n_pools = len(config.pools)
    return (
        f"Cleo is watching {n_pools} pool(s) via {config.endpoint}\n"
        f"Cycle every {config.poll_interval_seconds}s. "
        f"Analysis only — Cleo reports, you decide.\n"
        f"Ctrl-C to stop."
    )


async def run_modes(client: DefiMindClient, config: Config) -> None:
    """Run Cleo's active modes for one cycle. Today: monitoring only."""
    await monitoring.run(client, config)
