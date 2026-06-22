"""DeFiMind MCP endpoint client — spin-out-ready.

Two concerns, both caller-agnostic and free of outward `defimind` imports:

  - `client.py` — a thin MCP transport (stdlib + the `mcp` SDK only).
  - `twin.py`   — local State Twin rehydration + offline primitive sweeps,
    backed by `defipy` (an OPTIONAL extra: `defimind[twin]`). Its defipy
    imports are deferred, so importing this package stays mcp-only.

Neither imports the rest of `defimind`, and neither imports AnchorRegistry.
"""

from defimind.client.client import DefiMindClient, extract_payload
from defimind.client.twin import (
    ContentHashMismatch,
    build,
    build_from_rpc,
    rehydrate,
    sweep,
    verify_content_hash,
)

__all__ = [
    "DefiMindClient",
    "extract_payload",
    "rehydrate",
    "build",
    "sweep",
    "build_from_rpc",
    "verify_content_hash",
    "ContentHashMismatch",
]
