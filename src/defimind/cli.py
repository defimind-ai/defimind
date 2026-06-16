"""Console entry point for the `defimind` command.

Parses minimal args (just an optional --config) and hands off to the runner.
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from defimind.orchestration.runner import main


def run() -> None:
    parser = argparse.ArgumentParser(
        prog="defimind",
        description="StateTwins — DeFiMind's Uniswap position monitor (monitoring). Analysis only.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to config.toml (default: ./config.toml in the current directory).",
    )
    args = parser.parse_args()
    try:
        asyncio.run(main(args.config))
    except KeyboardInterrupt:
        print("\nStateTwins stopped.")


if __name__ == "__main__":
    run()
