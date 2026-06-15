"""
Cleo — a DeFiMind LP analyst agent.
═══════════════════════════════════════════════════════════════════════════════

Cleo is a thin, framework-less reference client for the hosted DeFiMind MCP
endpoint (https://mcp.defimind.ai/mcp). On a schedule, she asks DeFiMind's
hosted tools to inspect a list of Uniswap pools, and reports what they return.

She watches and reports. She does NOT trade, rebalance, or move funds.
Analysis only — you make every decision.

How the work is split:
  • Cleo (this file) holds the loop: read config, call tools, report, sleep.
  • The DeFiMind endpoint does the chain reads (through YOUR rpc_url) and the
    AMM math. Cleo sends a pool address + your RPC; the server does the rest.
  • Nothing here imports defipy or does DeFi math locally. By design.

Powered by DeFiMind · mcp.defimind.ai · built on DeFiPy State Twins.
Apache-2.0.

─── A note on what's verified ──────────────────────────────────────────────────
This is a reference skeleton. Two things should be confirmed against a live run,
and are marked [VERIFY] in the code below:
  1. The exact MCP client import/call API of the `mcp` SDK version you install.
  2. The exact field names returned by CheckPoolHealth / DetectRugSignals — the
     alerting logic prints full results first so you can see the real shape, then
     wire thresholds to the actual fields. Cleo errs toward printing, not guessing.
───────────────────────────────────────────────────────────────────────────────

This is the Phase-0 single-module body: the proven cleo.py logic, adapted only
so a packaged install resolves config.toml from the current working directory
(a packaged install has no co-located config file). Clean decomposition into
submodules is Phase 1.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# [VERIFY] Import paths for the official MCP Python SDK. These match the current
# SDK's streamable-HTTP client; if `pip install mcp` gives you a different
# layout, adjust these two imports (everything else stays the same).
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


# A packaged install has no config co-located with the module, so resolve from
# the current working directory instead of next to this file.
CONFIG_PATH = Path("config.toml")

# Tools Cleo uses for continuous monitoring. The endpoint also exposes
# AnalyzePosition, SimulatePriceMove, and CalculateSlippage — add them here (and
# in analyze_pool) if you want them in the loop.
MONITORING_TOOLS = ("CheckPoolHealth", "DetectRugSignals")


# ── Config ───────────────────────────────────────────────────────────────────

def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        sys.exit(
            f"No config.toml found at {CONFIG_PATH.resolve()}.\n"
            f"Copy the example first:  cp config.example.toml config.toml\n"
            f"then edit it with your RPC URL and pools."
        )
    with CONFIG_PATH.open("rb") as f:
        cfg = tomllib.load(f)

    # Let the RPC URL come from the environment, so the secret can stay out of
    # config.toml entirely. RPC_URL (if set) wins over whatever the file holds.
    env_rpc = os.environ.get("RPC_URL")
    if env_rpc:
        cfg["rpc_url"] = env_rpc

    # Minimal validation — fail loudly and early rather than mid-loop.
    for key in ("rpc_url", "endpoint", "poll_interval_seconds"):
        if key not in cfg:
            sys.exit(f"config.toml is missing required key: {key!r}")
    if "YOUR_KEY_HERE" in cfg["rpc_url"]:
        sys.exit("Edit config.toml — rpc_url still has the placeholder key.")
    if not cfg.get("pools"):
        sys.exit("config.toml has no [[pools]] blocks — nothing to watch.")
    return cfg


# ── Result handling ──────────────────────────────────────────────────────────

def extract_payload(result: Any) -> Any:
    """Pull a usable Python object out of an MCP CallToolResult.

    Prefers structured content; falls back to parsing text content as JSON;
    finally falls back to raw text. Defensive on purpose — different tools /
    SDK versions surface results slightly differently.
    """
    # Structured output, if the tool/SDK provides it.
    structured = getattr(result, "structuredContent", None)
    if structured:
        return structured

    # Otherwise, concatenate any text content blocks.
    texts: list[str] = []
    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            texts.append(text)
    joined = "\n".join(texts).strip()

    if not joined:
        return {"_note": "empty result", "_raw": repr(result)}
    try:
        return json.loads(joined)
    except json.JSONDecodeError:
        return joined  # not JSON — hand back the text as-is


def check_alerts(tool: str, payload: Any) -> list[str]:
    """Return a list of human-readable alerts for a tool result.

    [VERIFY] The field names below are NOT yet wired to the real tool output,
    because that should be confirmed against a live response (run once, read the
    printed payload, then map these to the actual keys). Until then, Cleo prints
    every result in full (see report_pool) so you never miss anything — this
    function only adds explicit ALERT lines once you've wired it.

    Example of what you'd add after seeing real output, e.g. for DetectRugSignals:

        if tool == "DetectRugSignals" and isinstance(payload, dict):
            for flag, tripped in payload.get("signals", {}).items():
                if tripped:
                    alerts.append(f"rug signal tripped: {flag}")
    """
    alerts: list[str] = []
    # Intentionally empty until thresholds are wired to real fields. Print-first.
    return alerts


# ── The loop ─────────────────────────────────────────────────────────────────

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


def report_pool(pool_label: str, tool: str, payload: Any, alerts: list[str]) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    print(f"\n[{ts}] {pool_label} — {tool}")
    if isinstance(payload, (dict, list)):
        print(json.dumps(payload, indent=2, default=str))
    else:
        print(payload)
    for a in alerts:
        print(f"  ⚠ ALERT: {a}")


async def analyze_pool(session: ClientSession, pool: dict[str, Any], rpc_url: str) -> None:
    label = pool.get("label", pool["address"])
    args = tool_args(pool, rpc_url)
    for tool in MONITORING_TOOLS:
        try:
            # [VERIFY] call_tool signature for your installed SDK version.
            result = await session.call_tool(tool, arguments=args)
        except Exception as e:  # noqa: BLE001 — a bad call on one pool/tool
            print(f"  ✗ {label} — {tool} failed: {e}")
            continue
        payload = extract_payload(result)
        alerts = check_alerts(tool, payload)
        report_pool(label, tool, payload, alerts)


async def run_cycle(cfg: dict[str, Any]) -> None:
    endpoint = cfg["endpoint"]
    rpc_url = cfg["rpc_url"]
    pools = cfg["pools"]

    # Open one MCP session per cycle, analyze every pool, then close it.
    async with streamablehttp_client(endpoint) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            for pool in pools:
                await analyze_pool(session, pool, rpc_url)


async def main() -> None:
    cfg = load_config()
    interval = cfg["poll_interval_seconds"]
    n_pools = len(cfg["pools"])
    print(
        f"Cleo is watching {n_pools} pool(s) via {cfg['endpoint']}\n"
        f"Cycle every {interval}s. Analysis only — Cleo reports, you decide.\n"
        f"Ctrl-C to stop."
    )
    while True:
        try:
            await run_cycle(cfg)
        except Exception as e:  # noqa: BLE001 — one bad cycle shouldn't kill Cleo
            print(f"\n✗ cycle error (will retry next interval): {e}")
        await asyncio.sleep(interval)
