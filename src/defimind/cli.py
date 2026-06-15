"""Console entry point for the `defimind` command.

Thin wrapper: run the app's async main loop, exit cleanly on Ctrl-C.
"""

from __future__ import annotations

import asyncio

from defimind._app import main


def run() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCleo stopped.")


if __name__ == "__main__":
    run()
