"""SPEC 1.4 — local State Twin rehydration + offline primitive sweeps.

Fully offline: snapshots come from defipy's MockProvider recipes (no RPC), the
BuildStateTwin wire form is reconstructed locally, and every sweep runs the
real defipy primitives against a built Exchange with zero chain reads.
"""

import hashlib
import json
import pathlib
from dataclasses import asdict

import pytest

# defipy is the optional [twin] extra. On an mcp-only base install it's absent,
# so skip this whole module gracefully rather than erroring at collection.
pytest.importorskip(
    "defipy", reason="twin tests require the [twin] extra (pip install defimind[twin])")

from defipy.twin import MockProvider
from defipy.primitives.position import (
    SimulatePriceMove,
    SimulateBalancerPriceMove,
    SimulateStableswapPriceMove,
)
from defimind.client import twin
from defimind import client as client_pkg


# ─── Wire form (mirrors defimind-mcp BuildStateTwin / SPEC 1.3 exactly) ──────

def _wire(snap) -> dict:
    body = asdict(snap)
    content_hash = "0x" + hashlib.sha256(
        json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()
    return {"__type__": type(snap).__name__, **body, "content_hash": content_hash}


# (MockProvider recipe, expected snapshot class, expected built Exchange class)
_RECIPES = [
    ("eth_dai_v2", "V2PoolSnapshot", "UniswapExchange"),
    ("eth_dai_v3", "V3PoolSnapshot", "UniswapV3Exchange"),
    ("eth_dai_balancer_50_50", "BalancerPoolSnapshot", "BalancerExchange"),
    ("usdc_dai_stableswap_A10", "StableswapPoolSnapshot", "StableswapExchange"),
]
_IDS = [r[0] for r in _RECIPES]


def _sweep_inputs(recipe, snap):
    """Per-type primitive + scenario param + scenario vector + fixed kwargs.
    V3 needs the snapshot's ticks (the hosted tool defaults them server-side;
    the package hands the caller the snapshot, so the ticks are in hand)."""
    if recipe == "eth_dai_v2":
        return (SimulatePriceMove(), "price_change_pct",
                [-0.30, -0.10, 0.0, 0.20], {"position_size_lp": 100.0})
    if recipe == "eth_dai_v3":
        return (SimulatePriceMove(), "price_change_pct",
                [-0.30, 0.0, 0.20],
                {"position_size_lp": 100.0,
                 "lwr_tick": snap.lwr_tick, "upr_tick": snap.upr_tick})
    if recipe == "eth_dai_balancer_50_50":
        return (SimulateBalancerPriceMove(), "price_change_pct",
                [-0.30, -0.10, 0.20], {"lp_init_amt": 10.0})
    return (SimulateStableswapPriceMove(), "price_change_pct",
            [-0.02, -0.01, 0.01], {"lp_init_amt": 100.0})


# ─── Rehydration round-trip (all four pool types) ────────────────────────────

@pytest.mark.parametrize("recipe,cls_name,_ex", _RECIPES, ids=_IDS)
def test_rehydrate_roundtrips_wire(recipe, cls_name, _ex):
    snap = MockProvider().snapshot(recipe)
    out = twin.rehydrate(_wire(snap))
    assert type(out).__name__ == cls_name
    assert out == snap                       # exact dataclass round-trip


def test_rehydrate_passes_through_bare_snapshot():
    snap = MockProvider().snapshot("eth_dai_v2")
    assert twin.rehydrate(snap) is snap      # not a dict → returned unchanged


def test_rehydrate_missing_type_errors():
    with pytest.raises(ValueError, match="__type__"):
        twin.rehydrate({"pool_id": "x", "content_hash": "0xabc"})


def test_rehydrate_unknown_type_errors():
    with pytest.raises(ValueError, match="unknown snapshot type"):
        twin.rehydrate({"__type__": "NotASnapshot", "pool_id": "x"})


# ─── build() → runnable Exchange (all four pool types) ───────────────────────

@pytest.mark.parametrize("recipe,_cls,ex_name", _RECIPES, ids=_IDS)
def test_build_produces_runnable_exchange(recipe, _cls, ex_name):
    snap = MockProvider().snapshot(recipe)
    ex = twin.build(_wire(snap))
    assert type(ex).__name__ == ex_name
    # "Runnable": the type-appropriate primitive sweeps it and returns results.
    prim, param, vals, fixed = _sweep_inputs(recipe, snap)
    results = twin.sweep(prim, ex, param, vals, **fixed)
    assert len(results) == len(vals)


def test_build_accepts_bare_snapshot():
    snap = MockProvider().snapshot("eth_dai_v2")
    ex = twin.build(snap)                     # dict OR snapshot both accepted
    assert type(ex).__name__ == "UniswapExchange"


# ─── Local primitive loop: one build, N evals, ordered, ZERO RPC ─────────────

@pytest.mark.parametrize("recipe,_cls,_ex", _RECIPES, ids=_IDS)
def test_sweep_is_ordered(recipe, _cls, _ex):
    snap = MockProvider().snapshot(recipe)
    ex = twin.build(_wire(snap))
    prim, param, vals, fixed = _sweep_inputs(recipe, snap)
    results = twin.sweep(prim, ex, param, vals, **fixed)
    # new_price_ratio == 1 + price_change_pct, so it is monotone + distinct
    # per entry — a clean proof the results are aligned to the input order.
    for v, r in zip(vals, results):
        assert r.new_price_ratio == pytest.approx(1.0 + v, abs=1e-9)


def test_sweep_runs_with_zero_rpc(monkeypatch):
    # Hard guard: if anything in build()/sweep() tried to construct a chain
    # client, this make_client stub would blow up. It must NOT be reached.
    import defipy.twin._rpc as rpc

    def _boom(*a, **k):
        raise AssertionError("RPC client constructed — sweep must be offline")
    monkeypatch.setattr(rpc, "make_client", _boom)

    ex = twin.build(_wire(MockProvider().snapshot("eth_dai_v2")))
    results = twin.sweep(SimulatePriceMove(), ex, "price_change_pct",
                         [-0.30, -0.10, 0.0, 0.20], position_size_lp=100.0)
    assert [round(r.new_price_ratio, 2) for r in results] == [0.7, 0.9, 1.0, 1.2]


def test_sweep_handles_calculate_slippage_signature():
    # CalculateSlippage's scenario input (amount_in) is NOT its first arg
    # (token_in precedes it). Keyword injection must still wrap it cleanly.
    from defipy.primitives.execution import CalculateSlippage
    snap = MockProvider().snapshot("eth_dai_v2")
    ex = twin.build(_wire(snap))
    tok = ex.factory.token_from_exchange[ex.name][ex.token0]
    results = twin.sweep(CalculateSlippage(), ex, "amount_in",
                         [1.0, 10.0, 100.0], token_in=tok)
    assert len(results) == 3
    # Larger trade → more slippage (monotone), confirming per-entry alignment.
    slips = [r.slippage_pct for r in results]
    assert slips[0] < slips[1] < slips[2]


# ─── content_hash verification ───────────────────────────────────────────────

def test_verify_content_hash_valid():
    wire = _wire(MockProvider().snapshot("eth_dai_v3"))
    assert twin.verify_content_hash(wire) is True
    # verify=True path also succeeds and returns the snapshot.
    snap = twin.rehydrate(wire, verify=True)
    assert type(snap).__name__ == "V3PoolSnapshot"


def test_verify_content_hash_detects_tamper():
    wire = _wire(MockProvider().snapshot("eth_dai_v2"))
    wire["reserve0"] = wire["reserve0"] * 2          # tamper, keep old hash
    assert twin.verify_content_hash(wire) is False
    with pytest.raises(twin.ContentHashMismatch):
        twin.rehydrate(wire, verify=True)
    # Without verify, rehydration still proceeds (caller opted out).
    assert twin.rehydrate(wire).reserve0 == wire["reserve0"]


def test_verify_no_hash_returns_false():
    snap = MockProvider().snapshot("eth_dai_v2")
    body = asdict(snap)
    assert twin.verify_content_hash({"__type__": "V2PoolSnapshot", **body}) is False


# ─── BYO-RPC local build path (wired, no real chain) ─────────────────────────

def test_build_from_rpc_wires_liveprovider(monkeypatch):
    import defipy.twin as dt
    captured = {}
    snap = MockProvider().snapshot("eth_dai_v2")

    class _FakeLP:
        def __init__(self, url):
            captured["url"] = url

        def snapshot(self, pool_id, **kw):
            captured["pool_id"] = pool_id
            captured["kw"] = kw
            return snap

    monkeypatch.setattr(dt, "LiveProvider", _FakeLP)
    ex = twin.build_from_rpc("uniswap_v2:0xabc", "http://rpc", block_number=123)
    assert captured == {"url": "http://rpc", "pool_id": "uniswap_v2:0xabc",
                        "kw": {"block_number": 123}}
    assert type(ex).__name__ == "UniswapExchange"


# ─── Spin-out purity: client/ is AR-agnostic with no outward defimind imports ─

def test_client_pkg_has_no_outward_defimind_or_ar_imports():
    cdir = pathlib.Path(client_pkg.__file__).parent
    files = list(cdir.glob("*.py"))
    assert files
    for f in files:
        for raw in f.read_text().splitlines():
            s = raw.strip()
            if not (s.startswith("import ") or s.startswith("from ")):
                continue
            assert "anchor" not in s.lower(), "AR import in {}: {}".format(f.name, s)
            if "defimind" in s:
                assert "defimind.client" in s, \
                    "outward defimind import in {}: {}".format(f.name, s)


def test_twin_defipy_imports_are_deferred():
    # defipy must be imported lazily (inside functions) so `import
    # defimind.client` works on the mcp-only base install.
    src = pathlib.Path(twin.__file__).read_text()
    for raw in src.splitlines():
        if "defipy" in raw and ("import " in raw):
            assert raw[:1] in (" ", "\t"), \
                "defipy import must be deferred (indented): {!r}".format(raw)
