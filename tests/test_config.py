"""Config loading + validation tests."""

import pytest

from defimind.config import load_config

VALID = """\
rpc_url = "https://eth-mainnet.example.com/v2/realkey"
endpoint = "https://mcp.defimind.ai/mcp"
poll_interval_seconds = 60

[[pools]]
label = "USDC/WETH"
address = "0xabc"
pool_type = "uniswap_v3"
chain_id = 1
"""


def _write(tmp_path, content):
    p = tmp_path / "config.toml"
    p.write_text(content)
    return p


def test_valid_config_loads(tmp_path, monkeypatch):
    monkeypatch.delenv("RPC_URL", raising=False)
    cfg = load_config(_write(tmp_path, VALID))
    assert cfg.endpoint == "https://mcp.defimind.ai/mcp"
    assert cfg.poll_interval_seconds == 60
    assert len(cfg.pools) == 1
    assert cfg.pools[0]["address"] == "0xabc"


def test_missing_key_fails(tmp_path, monkeypatch):
    monkeypatch.delenv("RPC_URL", raising=False)
    bad = VALID.replace('endpoint = "https://mcp.defimind.ai/mcp"\n', "")
    with pytest.raises(SystemExit):
        load_config(_write(tmp_path, bad))


def test_placeholder_rpc_fails(tmp_path, monkeypatch):
    monkeypatch.delenv("RPC_URL", raising=False)
    bad = VALID.replace("realkey", "YOUR_KEY_HERE")
    with pytest.raises(SystemExit):
        load_config(_write(tmp_path, bad))


def test_no_pools_fails(tmp_path, monkeypatch):
    monkeypatch.delenv("RPC_URL", raising=False)
    bad = VALID.split("[[pools]]")[0]
    with pytest.raises(SystemExit):
        load_config(_write(tmp_path, bad))


def test_missing_file_fails(tmp_path, monkeypatch):
    monkeypatch.delenv("RPC_URL", raising=False)
    with pytest.raises(SystemExit):
        load_config(tmp_path / "does_not_exist.toml")


def test_env_rpc_overrides_placeholder(tmp_path, monkeypatch):
    # RPC_URL env wins, so a placeholder file still loads.
    monkeypatch.setenv("RPC_URL", "https://real.example/key")
    placeholder = VALID.replace("realkey", "YOUR_KEY_HERE")
    cfg = load_config(_write(tmp_path, placeholder))
    assert cfg.rpc_url == "https://real.example/key"
