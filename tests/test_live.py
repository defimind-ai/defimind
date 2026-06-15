"""Live-RPC gate — confirms a real monitoring cycle completes end to end.

Skipped unless DEFIMIND_TEST_RPC_URL is set to an Ethereum-mainnet RPC, so the
default `pytest` run stays offline and deterministic. Run:

    DEFIMIND_TEST_RPC_URL="https://eth-mainnet.../v2/<key>" \\
        .venv/bin/pytest tests/test_live.py -v

Drives the real DefiMindClient against the hosted endpoint with a real mainnet
V3 pool (USDC/WETH 0.05%) — no fakes — exercising the same path `defimind` runs.
"""

import asyncio
import os

import pytest

from defimind.client import DefiMindClient
from defimind.modes.monitoring import check_alerts, tool_args

RPC = os.environ.get("DEFIMIND_TEST_RPC_URL")
pytestmark = pytest.mark.skipif(
    not RPC, reason="set DEFIMIND_TEST_RPC_URL to run the live gate")

ENDPOINT = "https://mcp.defimind.ai/mcp"
USDC_WETH_V3 = {
    "address": "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640",
    "pool_type": "uniswap_v3",
    "chain_id": 1,
}


def _call(tool, args):
    async def go():
        client = DefiMindClient(ENDPOINT)
        async with client.session() as conn:
            return await conn.call_tool(tool, args)
    return asyncio.run(go())


def test_pool_health_v3_live():
    payload = _call("CheckPoolHealth", tool_args(USDC_WETH_V3, RPC))
    assert isinstance(payload, dict)
    assert payload["tvl_in_token0"] > 0


def test_rug_signals_v3_live():
    payload = _call("DetectRugSignals", tool_args(USDC_WETH_V3, RPC))
    assert isinstance(payload, dict)
    # The contract alerts wire to: each rug flag is a top-level boolean.
    for flag in ("tvl_suspiciously_low", "single_sided_concentration",
                 "inactive_with_liquidity"):
        assert isinstance(payload[flag], bool)
    # check_alerts must run cleanly on real output (returns a list).
    assert isinstance(check_alerts("DetectRugSignals", payload), list)
