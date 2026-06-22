"""Monitoring mode — the only mode at MVP-A.

Given a connected client + config, build each tool's arguments, call the
monitoring tools, derive alerts, and report. Print-first: the full payload is
always shown; alerts are additive.

The endpoint exposes eleven tools in total. The two wired here (CheckPoolHealth,
DetectRugSignals) are the V2/V3 watch tools suited to a continuous loop. The other
nine are on-demand: eight reactive analysis tools (V2/V3 position/price/slippage,
plus Balancer and Stableswap position/price/depeg), and BuildStateTwin, which returns
a serialized State Twin for local, off-MCP analysis. They take different args and pool
types, so they belong in a future analysis mode, not this monitoring loop. The client
can already call any of them.
"""

from __future__ import annotations

from typing import Any

from defimind.client import DefiMindClient
from defimind.config import Config
from defimind.report import report_pool

# Tools StateTwins uses for continuous monitoring.
MONITORING_TOOLS = ("CheckPoolHealth", "DetectRugSignals")

# DetectRugSignals represents each rug signal as its OWN top-level boolean key
# (confirmed against live output in Phase 0 — not a nested dict, not a list).
# These three booleans are the firm contract alerts wire to.
RUG_FLAGS = (
    "tvl_suspiciously_low",
    "single_sided_concentration",
    "inactive_with_liquidity",
)


def tool_args(pool: dict[str, Any], rpc_url: str) -> dict[str, Any]:
    """Build the argument dict every DeFiMind tool expects (BYO-RPC contract)."""
    args = {
        "pool_address": pool["address"],
        "rpc_url": rpc_url,
        "pool_type": pool["pool_type"],
    }
    if "chain_id" in pool:
        args["chain_id"] = pool["chain_id"]
    return args


def check_alerts(tool: str, payload: Any) -> list[str]:
    """Return human-readable alerts for a tool result.

    Wired to the real DetectRugSignals fields captured in Phase 0: each rug
    signal is a top-level boolean; `risk_level` is an aggregate severity string.
    The booleans are the firm contract; `risk_level`'s full range is treated as
    advisory (only "high" is escalated) until more pools are observed.
    """
    alerts: list[str] = []
    if tool == "DetectRugSignals" and isinstance(payload, dict):
        for flag in RUG_FLAGS:
            if payload.get(flag):
                alerts.append(f"rug signal tripped: {flag}")
        if payload.get("risk_level") == "high":
            alerts.append("risk_level: high")
    return alerts


async def run(client: DefiMindClient, config: Config) -> None:
    """Run one monitoring pass over every configured pool."""
    for pool in config.pools:
        label = pool.get("label", pool["address"])
        args = tool_args(pool, config.rpc_url)
        for tool in MONITORING_TOOLS:
            try:
                payload = await client.call_tool(tool, args)
            except Exception as e:  # noqa: BLE001 — a bad call on one pool/tool
                print(f"  ✗ {label} — {tool} failed: {e}")
                continue
            alerts = check_alerts(tool, payload)
            report_pool(label, tool, payload, alerts)
