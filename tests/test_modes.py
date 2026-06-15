"""Monitoring-mode tests — alert wiring + tool args."""

from defimind.modes.monitoring import check_alerts, tool_args

# Known-bad DetectRugSignals payload captured live in Phase 0:
# single_sided_concentration tripped (top LP holds 100%).
KNOWN_BAD = {
    "tvl_suspiciously_low": False,
    "single_sided_concentration": True,
    "inactive_with_liquidity": False,
    "signals_detected": 1,
    "risk_level": "medium",
}

HEALTHY = {
    "tvl_suspiciously_low": False,
    "single_sided_concentration": False,
    "inactive_with_liquidity": False,
    "signals_detected": 0,
    "risk_level": "low",
}


def test_alerts_fire_on_known_bad():
    alerts = check_alerts("DetectRugSignals", KNOWN_BAD)
    assert any("single_sided_concentration" in a for a in alerts)


def test_alerts_quiet_on_healthy():
    assert check_alerts("DetectRugSignals", HEALTHY) == []


def test_high_risk_level_escalates():
    payload = {**HEALTHY, "risk_level": "high"}
    assert any("risk_level" in a for a in check_alerts("DetectRugSignals", payload))


def test_checkpoolhealth_has_no_alerts():
    # Alerts wire to DetectRugSignals only; CheckPoolHealth is print-only.
    assert check_alerts("CheckPoolHealth", {"has_activity": False}) == []


def test_tool_args_includes_chain_id():
    a = tool_args({"address": "0x1", "pool_type": "uniswap_v3", "chain_id": 1}, "https://rpc")
    assert a == {
        "pool_address": "0x1",
        "rpc_url": "https://rpc",
        "pool_type": "uniswap_v3",
        "chain_id": 1,
    }


def test_tool_args_omits_missing_chain_id():
    a = tool_args({"address": "0x1", "pool_type": "uniswap_v2"}, "https://rpc")
    assert "chain_id" not in a
