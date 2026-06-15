"""DeFiMind MCP endpoint client — spin-out-ready.

Imports stdlib + the `mcp` SDK only; nothing from the rest of `defimind`.
Caller-agnostic: it's a *DeFiMind endpoint client*, not a Cleo/agent thing.
"""

from defimind.client.client import DefiMindClient, extract_payload

__all__ = ["DefiMindClient", "extract_payload"]
