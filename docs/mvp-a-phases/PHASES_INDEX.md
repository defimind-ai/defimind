# MVP-A Phases — `defimind` package (Cleo agent) → public

*Hand-off specs for Claude Code. Scope: build the **free, installable `defimind`
agent package** — with **Cleo** as an agent submodule — from an empty repo to a
**public, `pip install`-able** release. The paid tier (`defimind-api`, credit
ledger, gasless sessions, Stripe, paid-compute gate) is **deferred** — not in this
phase set.*

*Captured: June 14, 2026. Supersedes the earlier `cleo/`-as-standalone-clone-and-fork
phase set — see "Direction" below.*

---

## Direction (read first)

The agent is **not** a standalone clone-and-fork repo. It is a **proper installable
Python package** living in the pre-existing `defimind-ai/defimind` repo, structured
exactly like the sibling `defimind-mcp` package already is (`src/` layout,
`pyproject.toml`, console entry point, real tests, Apache-2.0). This is a **product
component**, versioned and dependable — not a hackathon artifact.

- **`defimind`** = the installable agent package (`pip install defimind` →
  `defimind` console command).
- **Cleo** = the agent **persona**, living as a submodule **`defimind.agents.cleo`**.
  "It's always Cleo, in different modes" — the modes are package capabilities, not
  forks.
- The package **consumes** the live `defimind-mcp` endpoint as a thin client. It
  does **not** import `defipy` or do any DeFi math / chain reads locally — that all
  lives behind the endpoint.

There is a working single-file reference (`/Users/ian_moore/repos/cleo/cleo.py`)
whose **logic is correct and proven in shape** (config → MCP session → call tools →
report → loop). These phases **decompose that working logic into the package
structure** below — reuse it, don't reinvent it. After the phases are complete and
verified, the `cleo/` directory will be **deleted** (it was the prototype).

---

## Target package structure

Mirrors `defimind-mcp` conventions (`src/` layout, setuptools, console script):

```
defimind/                         # repo root (defimind-ai/defimind; LICENSE already present)
  pyproject.toml                  # name="defimind", console script, dep on mcp (NOT defipy)
  README.md                       # package README (written alongside these phases)
  src/
    defimind/
      __init__.py
      cli.py                      # console entry point: defimind = defimind.cli:run
      client/                     # MCP transport. SPIN-OUT-READY: depends on nothing
        __init__.py               #   else in defimind. Future `defimind-client` SDK seed.
        client.py
      config/                     # config loading + validation
        __init__.py
        config.py
      modes/                      # reasoning modes; one question-shape each
        __init__.py
        monitoring.py             # the only mode at MVP-A
      orchestration/              # THIN coordination seam (grows at MVP-B/C)
        __init__.py
        runner.py
      report/                     # result -> human-readable; MVP-C hooks anchoring here
        __init__.py
        report.py
      agents/
        __init__.py
        cleo.py                   # the Cleo persona: wires modes + voice + identity
  tests/
    test_client.py
    test_config.py
    test_modes.py
  config.example.toml
  .gitignore
  LICENSE                         # already present (Apache-2.0)
```

> The exact internal split can flex during the build, but two structural rules are
> **non-negotiable** (see Phase 1): `client/` imports nothing else from `defimind`
> (spin-out readiness), and nothing imports `defipy` or web3/chain libs (thin-client
> boundary).

---

## Phase list

| Phase | Name | One-line goal | Gate to advance |
|---|---|---|---|
| **0** | Package scaffold & first contact | Stand up the `src/defimind` package skeleton + `pyproject.toml`; install it; run the existing `cleo.py` logic against the **live** endpoint and **capture real tool output**. | Package installs (`pip install -e .`); `defimind` command runs the monitoring loop end-to-end; real `CheckPoolHealth`+`DetectRugSignals` payloads captured (resolves the two `[VERIFY]` unknowns). |
| **1** | Decompose into submodules | Refactor the working logic into `client/`, `config/`, `modes/monitoring`, `orchestration/runner`, `report/`, `agents/cleo`, `cli`. Enforce the two structural rules. Wire alerts to the real fields. | All submodules in place; `client/` has zero outward `defimind` imports; no `defipy` import anywhere; `defimind` command behaves identically to Phase 0; tests pass. |
| **2** | Package polish & tests | Real README example output; `pyproject.toml` metadata; test suite (offline + optional live gate, mirroring `defimind-mcp`); config hygiene; asset/icon. | `pip install` from a clean env → `defimind` runs to a real result following only the README; `pytest` green; metadata complete. |
| **3** | Public release | Push `defimind-ai/defimind` public; verify the install-to-result path for an outside user; metadata, links, secret hygiene. | Public repo live; `pip install` (from repo) → real result works for an outside user; no secrets in tree/history. |

Do the phases in order. Do not start a phase until the prior gate is met.

---

## Cross-cutting rules (every phase)

- **Analysis only.** Cleo reports; she never trades, rebalances, or moves funds.
  No phase changes this. No `execute`/`trade`/`sign-and-send` code path, ever.
- **Thin client, BYO-RPC, authless.** The package sends a pool address + the user's
  RPC to the live endpoint. No keys, no accounts, no signing for the free agent.
- **No `defipy` / web3 / chain libs as dependencies.** All DeFi math and chain reads
  live behind the endpoint. If a submodule needs one of these, the thin-client
  boundary is leaking — stop and flag.
- **`client/` is spin-out-ready.** It imports stdlib + the `mcp` SDK only — never
  anything else from `defimind`. Dependencies point *into* `client/`, never out.
  Anything it needs from the agent is passed in as an argument. Its public API and
  types are its own (no `defimind` `Config`/`Report` objects crossing the boundary).
- **Orchestration stays thin.** At MVP-A there is one mode; `orchestration/` is a
  small runner, not a framework. It earns weight at MVP-B/C when modes compose.
- **Mirror `defimind-mcp` conventions.** `src/` layout, setuptools, pinned/clear
  deps, console script, Apache-2.0, arXiv/homepage URLs, real `tests/`.
- **Secrets discipline.** `config.toml` (holds the user's RPC URL) is git-ignored and
  never committed. Never read or echo a real RPC URL into any doc, commit, or example.
- **Brand/arrow.** The package is `defimind`; the agent persona is **Cleo**
  (`defimind.agents.cleo`); it is **powered by** the DeFiMind endpoint (Cleo depends
  on DeFiMind, not the reverse).

## Explicitly deferred (not in this phase set)

`defimind-api`, credit ledger, gasless-signature sessions, Stripe, paid-compute
gate, wallet-connect, hosted browser widget (MVP-B), AnchorRegistry integration
(MVP-C), agent execution (permanent boundary). If a phase pulls toward any of these,
that's scope creep — stop and flag.
