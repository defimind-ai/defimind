"""Thin client for the hosted DeFiMind MCP endpoint.

SPIN-OUT-READY. This module imports the Python stdlib and the `mcp` SDK only —
nothing from elsewhere in `defimind`. The endpoint URL is passed in, so the
client stays caller-agnostic. Naming is chosen to survive extraction:
`from defimind.client import DefiMindClient` becomes `from defimind_client import
DefiMindClient` with no other change.

No `defipy` / web3 / chain imports — by design. This is a transport, not a
chain reader; the hosted endpoint does the chain reads and the AMM math.
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


def extract_payload(result: Any) -> Any:
    """Pull a usable Python object out of an MCP CallToolResult.

    Prefers structured content; falls back to parsing text content as JSON;
    finally falls back to raw text. Defensive on purpose — different tools /
    SDK versions surface results slightly differently. (Against the live
    DeFiMind endpoint, results arrive as JSON text, not structuredContent.)
    """
    structured = getattr(result, "structuredContent", None)
    if structured:
        return structured

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


class DefiMindClient:
    """Connect to a DeFiMind MCP endpoint and call its tools.

    Usage:
        client = DefiMindClient(endpoint)
        async with client.session() as conn:
            payload = await conn.call_tool("CheckPoolHealth", args)
    """

    def __init__(self, endpoint: str) -> None:
        self._endpoint = endpoint
        self._session: ClientSession | None = None

    @asynccontextmanager
    async def session(self):
        """Open one MCP session for the connection lifecycle; yields a connected self."""
        async with streamablehttp_client(self._endpoint) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                self._session = session
                try:
                    yield self
                finally:
                    self._session = None

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool within an open session and return its parsed payload."""
        if self._session is None:
            raise RuntimeError(
                "call_tool requires an open session(); use `async with client.session()`"
            )
        result = await self._session.call_tool(name, arguments=arguments)
        return extract_payload(result)
