"""Load and validate StateTwins' config.toml.

The config path resolves from the current working directory (a packaged install
has no co-located config). The RPC URL may also come from the RPC_URL
environment variable, which wins over whatever the file holds — so the secret
can stay out of config.toml entirely.
"""

from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path("config.toml")


@dataclass
class Config:
    rpc_url: str
    endpoint: str
    poll_interval_seconds: int
    pools: list[dict[str, Any]]


def load_config(path: Path | None = None) -> Config:
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.exists():
        sys.exit(
            f"No config.toml found at {config_path.resolve()}.\n"
            f"Copy the example first:  cp config.example.toml config.toml\n"
            f"then edit it with your RPC URL and pools."
        )
    with config_path.open("rb") as f:
        cfg = tomllib.load(f)

    # RPC_URL (if set) wins over the file — keeps the secret out of config.toml.
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

    return Config(
        rpc_url=cfg["rpc_url"],
        endpoint=cfg["endpoint"],
        poll_interval_seconds=cfg["poll_interval_seconds"],
        pools=cfg["pools"],
    )
