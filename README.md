# defimind

**DeFiMind's analyst agent — Cleo.** She observes your Uniswap liquidity
positions, consults DeFiMind's hosted analytics, and reports her findings so you can
make informed decisions.

She watches and reports. **She does not trade, rebalance, or move funds — you make
every decision.** Think of her as a tireless quant analyst looking over your
positions, not a bot that manages your money.

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3776ab)](https://www.python.org)
[![arXiv](https://img.shields.io/badge/arXiv-2605.11522-b31b1b.svg)](https://arxiv.org/abs/2605.11522)

> Powered by **DeFiMind** · [`mcp.defimind.ai`](https://mcp.defimind.ai/mcp) · built on the open-source [DeFiPy](https://defipy.org) **State Twins** substrate.

Cleo is named for the Muse of history — the recorder of the DeFi substrate.

---

## What this is

`defimind` is an **installable Python agent**. Cleo, its analyst persona, runs a
loop: she reads the pools you configure, asks the hosted **DeFiMind MCP endpoint** to
inspect them, and reports what comes back — pool health and rug signals on a
schedule, with the full analysis printed every cycle.

The work is split deliberately:

- **The agent (this package)** holds the loop: read config, call the endpoint,
  report, repeat. It's a **thin client** — a few hundred readable lines.
- **The DeFiMind endpoint** does the chain reads (through *your* RPC) and the AMM
  math. The agent sends a pool address and your RPC URL; the server does the rest.
- **Nothing here imports DeFiPy or does DeFi math locally.** By design — the math
  lives behind the endpoint, open-source and verifiable at [defipy.org](https://defipy.org).

**Analysis only.** Cleo surfaces information; she never decides or executes. The
decision is always yours.

## Install

```bash
pip install .                      # from a clone of this repo
# or, for development:
pip install -e ".[dev]"
```

This installs the `defimind` console command.

## Quickstart (the 10-minute path)

```bash
# 1. Configure: copy the example and fill in your RPC + pools
cp config.example.toml config.toml
#    edit config.toml — add your RPC URL and the pools you want watched

# 2. Run
defimind
```

On each cycle, Cleo prints a health + rug-signal read on every pool in your
watchlist: watch, analyze, report, wait, repeat.

> **Heads up:** you supply your own RPC URL (it may contain an API key). It goes in
> `config.toml`, which is git-ignored. Never commit it.

## What you'll see

A real cycle against the hosted endpoint (USDC/WETH 0.05% V3, mainnet). When a
rug signal trips, Cleo prints the full payload and adds an `⚠ ALERT` line:

```
Cleo is watching 1 pool(s) via https://mcp.defimind.ai/mcp
Cycle every 60s. Analysis only — Cleo reports, you decide.
Ctrl-C to stop.

[2026-06-15 19:40:25Z] USDC/WETH 0.05% (V3) — CheckPoolHealth
{
  "version": "V3",
  "token0_name": "USDC",
  "token1_name": "WETH",
  "spot_price": 0.0005474970758436177,
  "reserve0": 257715436.32933998,
  "reserve1": 141098.44779007568,
  "total_liquidity": 6030194.693176328,
  "tvl_in_token0": 515430872.65867996,
  "num_lps": 1,
  "top_lp_share_pct": 1.0,
  "has_activity": false,
  "fee_pips": 500,
  "tvl_in_token1": 282196.89558015135,
  "tick_current": -75106
}

[2026-06-15 19:40:26Z] USDC/WETH 0.05% (V3) — DetectRugSignals
{
  "tvl_suspiciously_low": false,
  "single_sided_concentration": true,
  "inactive_with_liquidity": false,
  "signals_detected": 1,
  "risk_level": "medium",
  "details": [
    "single_sided_concentration: top LP holds 100.0% of supply (threshold 90.0%)",
    "inactive_with_liquidity: unavailable for V3 (no per-swap history)"
  ]
}
  ⚠ ALERT: rug signal tripped: single_sided_concentration
```

*(Trimmed for length — `CheckPoolHealth` also returns `total_fee0/1`,
`num_swaps`, `fee_accrual_rate_recent`; `DetectRugSignals` nests the full
`pool_health` block.)*

## How it works

```
  defimind (this package)             DeFiMind endpoint                 substrate
  ───────────────────────             ─────────────────                 ─────────
  read config.toml
  for each pool, each cycle:
    call a tool  ───────────────────▶ mcp.defimind.ai/mcp
                                      reads chain via your RPC  ──────▶  DeFiPy
                                      runs the analysis                 State Twins
    receive result  ◀───────────────  returns a typed result
    report / alert
  sleep, repeat
```

The agent is a **client**. The value — chain reads, AMM math, State Twins — lives on
the DeFiMind server. The agent stays thin and readable; every analysis is a call to
DeFiMind's hosted infrastructure. **The math is open; the reports are paid.**

### The tools she calls

The hosted endpoint exposes five tools over Uniswap V2/V3. The default monitoring
mode uses the two suited to continuous watching:

- **`CheckPoolHealth`** — TVL, reserves, LP concentration, recent activity.
- **`DetectRugSignals`** — threshold-based rug flags on a pool's on-chain state.

The other three — `AnalyzePosition`, `SimulatePriceMove`, `CalculateSlippage` — are
available at the same endpoint.

## Configuration

Everything the agent needs is in `config.toml` (copy from `config.example.toml`):

- `rpc_url` — your own RPC endpoint (the server reads chain state through it)
- `endpoint` — the DeFiMind MCP URL (defaults to the hosted server)
- `poll_interval_seconds` — how often to run a cycle
- a `[[pools]]` block per pool — `address`, `pool_type` (`uniswap_v2` /
  `uniswap_v3`), an optional `chain_id` guard, and a friendly `label`

## Scope boundary (please read)

Cleo produces **analysis**, not **advice** and not **action**. She does not tell you
to enter, exit, or rebalance a position, and she does not transact. She reports the
current state and risk of your positions; the decision is always yours. This is
intentional and permanent.

## Develop

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Tests (offline by default):
```bash
pytest tests/
```

Optional live gate (hits the real endpoint with a real pool; needs your own RPC):
```bash
DEFIMIND_TEST_RPC_URL="https://eth-mainnet.example/v2/<key>" pytest tests/test_live.py -v
```

## Roadmap

`defimind` v0.1 is the free monitoring agent. Cleo is built around **modes** (one
question-shape each); monitoring ships first, with screening, ensemble, comparative,
and treasury modes as the package grows. Heavier paid-compute analyses may later be
offered as a metered tier — a future, opt-in addition, not part of the free agent.

## License

Apache-2.0. See [LICENSE](LICENSE). Free to fork, modify, and build on.

## See also

- DeFiMind MCP endpoint: [`mcp.defimind.ai`](https://mcp.defimind.ai/mcp) · [defimind-mcp](https://github.com/defimind-ai/defimind-mcp)
- DeFiPy (open-source substrate): https://defipy.org
- DeFiMind: https://defimind.ai
- State Twins paper: https://arxiv.org/abs/2605.11522
