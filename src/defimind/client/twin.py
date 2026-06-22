"""Local State Twin rehydration + offline primitive sweeps — spin-out-ready.

The client side of the State Twins path: take a serialized twin (the
`BuildStateTwin` wire form, or a snapshot built locally) and rehydrate it into
a runnable defipy Exchange, then run primitive loops locally with ZERO RPC —
build once, run N counterfactuals client-side. This is the State Twins payoff.

SPIN-OUT-READY. Imports the Python stdlib and `defipy` only — nothing from the
rest of `defimind`, and no AnchorRegistry. Anchoring (submitting content_hash
anywhere) is an outer hook composed elsewhere, not here.

`defipy` is an OPTIONAL dependency: install `defimind[twin]` (which pulls
`defipy[chain]`) or `pip install defipy[chain]`. The defipy imports are
DEFERRED to call time so `import defimind.client` keeps working on the
mcp-only base install — only the functions below actually need defipy.
Hash verification (verify_content_hash) is pure stdlib and needs no defipy.

Wire format (the contract produced by defimind-mcp's BuildStateTwin, SPEC 1.3):

    { "__type__": "<SnapshotClass>", <all dataclass fields>,
      "content_hash": "0x" + sha256(json.dumps(<body>, sort_keys=True)) }
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

# Envelope keys added by the MCP serialization layer (SPEC 1.3); not part of
# the snapshot body. Stripped before reconstruction and before hashing.
_ENVELOPE_KEYS = ("__type__", "content_hash")


class ContentHashMismatch(ValueError):
    """Raised when a wire twin's content_hash does not match its body —
    a tampered or version-mismatched payload."""


def _body(wire: dict) -> dict:
    """The canonical snapshot body: the wire dict minus the envelope keys.
    This is exactly what the MCP layer hashed (asdict(snapshot))."""
    return {k: v for k, v in wire.items() if k not in _ENVELOPE_KEYS}


def _canonical_hash(body: dict) -> str:
    """Recompute content_hash over a snapshot body. MUST match the MCP layer
    byte-for-byte: sha256 over json.dumps(body, sort_keys=True)."""
    canonical = json.dumps(body, sort_keys=True).encode("utf-8")
    return "0x" + hashlib.sha256(canonical).hexdigest()


def verify_content_hash(wire: dict) -> bool:
    """True iff wire['content_hash'] matches a hash recomputed over the body.

    Returns False if the wire carries no content_hash (nothing to verify).
    Pure stdlib — does not import defipy."""
    expected = wire.get("content_hash")
    if expected is None:
        return False
    return _canonical_hash(_body(wire)) == expected


def rehydrate(wire: Any, *, verify: bool = False):
    """Rehydrate a serialized twin back into its defipy snapshot dataclass.

    Parameters
    ----------
    wire : dict
        The BuildStateTwin wire form: {"__type__", <fields>, "content_hash"}.
        A bare snapshot dataclass is passed through unchanged (convenience).
    verify : bool, default False
        If True, recompute content_hash over the body and raise
        ContentHashMismatch on mismatch BEFORE reconstructing.

    Returns
    -------
    A defipy.twin.snapshot.* dataclass instance (V2/V3/Balancer/Stableswap).
    """
    if not isinstance(wire, dict):
        return wire  # already a snapshot — pass through

    if verify and not verify_content_hash(wire):
        raise ContentHashMismatch(
            "content_hash does not match the twin body (tampered or "
            "version-mismatched payload)."
        )

    type_name = wire.get("__type__")
    if not type_name:
        raise ValueError("wire twin is missing its '__type__' discriminator.")

    # Deferred import — keeps `import defimind.client` working without defipy.
    from defipy.twin import snapshot as snapshot_module

    cls = getattr(snapshot_module, type_name, None)
    if cls is None:
        raise ValueError(
            "unknown snapshot type {!r}; not found in defipy.twin.snapshot."
            .format(type_name)
        )
    return cls(**_body(wire))


def build(wire_or_snapshot: Any, *, verify: bool = False):
    """Rehydrate (if needed) and build a runnable defipy Exchange.

    Accepts either a wire dict or an already-rehydrated snapshot. The returned
    Exchange is a first-class object — pass it to sweep() or directly to any
    defipy primitive's .apply(lp, ...). No RPC: StateTwinBuilder reconstructs
    the pool purely from snapshot state.
    """
    snap = (rehydrate(wire_or_snapshot, verify=verify)
            if isinstance(wire_or_snapshot, dict) else wire_or_snapshot)
    from defipy.twin import StateTwinBuilder
    return StateTwinBuilder().build(snap)


def sweep(primitive, exchange, scenario_param: str, values, **fixed):
    """Run one defipy ``primitive`` over a vector of scenario ``values`` against
    a single built ``exchange`` — one build, N evals, ZERO RPC. Results are
    returned in input order.

    Each value is injected as the keyword ``scenario_param``; ``fixed`` carries
    the primitive's other ``apply()`` kwargs. Keyword injection (rather than
    positional) is what lets this wrap *any* primitive — including ones whose
    scenario input isn't the first argument (e.g. CalculateSlippage, where
    token_in precedes amount_in).

    Examples
    --------
        ex = build(wire)                                   # built once

        # SimulatePriceMove across a price grid:
        from defipy.primitives.position import SimulatePriceMove
        results = sweep(SimulatePriceMove(), ex, "price_change_pct",
                        [-0.3, -0.1, 0.0, 0.2], position_size_lp=100.0)

        # CalculateSlippage across trade sizes (token_in is held fixed):
        from defipy.primitives.execution import CalculateSlippage
        results = sweep(CalculateSlippage(), ex, "amount_in",
                        [1_000.0, 5_000.0], token_in=tok)
    """
    return [primitive.apply(exchange, **{scenario_param: v, **fixed})
            for v in values]


def build_from_rpc(pool_id: str, rpc_url: str, **snapshot_kwargs):
    """BYO-RPC: build the same runnable twin locally from your own RPC, with no
    hosted BuildStateTwin in the loop — so the package is self-sufficient and
    the hosted tool is a convenience, not a chokepoint.

    ``pool_id`` is ``"<protocol>:<address>"`` (e.g. ``"uniswap_v2:0xB4e1…"``).
    ``snapshot_kwargs`` pass straight through to ``LiveProvider.snapshot``:
    ``block_number`` (all types), ``lwr_tick``/``upr_tick`` (uniswap_v3),
    ``n_coins`` (stableswap). Requires the chain extra
    (``pip install defipy[chain]`` or ``defimind[twin]``).
    """
    from defipy.twin import LiveProvider, StateTwinBuilder
    snap = LiveProvider(rpc_url).snapshot(pool_id, **snapshot_kwargs)
    return StateTwinBuilder().build(snap)
