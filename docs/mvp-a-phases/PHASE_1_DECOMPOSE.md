# Phase 1 — Decompose into Submodules

*Hand-off spec for Claude Code. Part of the MVP-A `defimind`-package phase set
(`PHASES_INDEX.md`). Do not start until Phase 0's gate is met — this phase needs
the package installing, the command running, and the real tool output captured.*

---

## Goal

Refactor the single working module from Phase 0 into the clean submodule structure,
enforcing the two non-negotiable structural rules, and wire alerts to the **real**
captured fields. Behavior must be **identical** to Phase 0 at the end — this is a
structure + wiring phase, not a feature phase.

## Target structure (from `PHASES_INDEX.md`)

```
src/defimind/
  __init__.py
  cli.py                  # defimind = defimind.cli:run → orchestration.runner
  client/                 # MCP transport — SPIN-OUT-READY
    __init__.py
    client.py
  config/
    __init__.py
    config.py
  modes/
    __init__.py
    monitoring.py         # the only mode at MVP-A
  orchestration/
    __init__.py
    runner.py             # THIN: load config → build client → run modes → loop
  report/
    __init__.py
    report.py
  agents/
    __init__.py
    cleo.py               # Cleo persona: ties modes + voice + identity together
```

## Where each piece of the Phase-0 logic goes

The proven functions from `cleo.py` / Phase-0 `_app.py` map cleanly:

| Phase-0 logic | Lands in |
|---|---|
| `streamablehttp_client` + `ClientSession` + `session.call_tool` + `extract_payload` | `client/client.py` |
| `load_config` + validation | `config/config.py` |
| `tool_args` + `check_alerts` (now wired) + `MONITORING_TOOLS` + per-pool loop | `modes/monitoring.py` |
| `run_cycle` + `main` loop/sleep/retry | `orchestration/runner.py` |
| `report_pool` (formatting) | `report/report.py` |
| Cleo identity, the monitoring intro line, mode selection | `agents/cleo.py` |
| `cli.run()` | `cli.py` |

## The two non-negotiable structural rules

1. **`client/` imports nothing else from `defimind`.** It imports stdlib + the
   `mcp` SDK only. It exposes a small public API and its own types. Concretely:
   - A class, e.g. `DefiMindClient(endpoint: str)`, with an async
     `call_tool(name: str, arguments: dict) -> Any` (returns the parsed payload via
     the `extract_payload` logic, which moves *into* the client), and an async
     context manager / `session()` for the connection lifecycle.
   - It must **not** import `defimind.config`, `defimind.modes`, etc. Anything it
     needs (the endpoint URL) is **passed in**. Naming should survive extraction:
     `from defimind.client import DefiMindClient` → trivially becomes
     `from defimind_client import DefiMindClient` later. No "agent"/"cleo" in client
     vocabulary — it's a *DeFiMind endpoint client*, caller-agnostic.

2. **No `defipy` / web3 / chain imports anywhere in the package.** Thin client only.
   If any submodule reaches for chain logic, the boundary is leaking — stop and flag.

## Tasks

1. **Create the submodule tree** and move the Phase-0 logic into it per the table
   above. Keep functions small and named as they were where sensible.

2. **Build `client/client.py` to the spin-out contract.** Fold `extract_payload`
   into it (parsing a tool result is the client's job). Public surface only:
   construct with endpoint, open session, `call_tool`, close. No outward imports.

2a. **Stamp every outgoing request with a client identifier (observability).** In
   `client/` — the single chokepoint every call flows through — set a distinctive
   header on all requests to the endpoint, e.g. `User-Agent: defimind-agent/<version>`
   (read the version from `defimind.__version__`) and/or a custom
   `X-DeFiMind-Client: cleo/<version>`. Purpose: let the operator see, in the
   endpoint's logs, what share of traffic comes from this package versus other MCP
   clients (Claude Desktop, Cursor, curl, etc.) — which feeds the cost/usage
   monitoring that gates the eventual paid tier (rising package traffic = real demand).
   - **This is a rough signal, NOT auth and NOT per-user.** A header is spoofable,
     and every install sends the *same* marker, so it cannot distinguish one user's
     runs from another's. It answers "how much of my traffic is the package," not
     "who" or "how do I bill." Per-user attribution is the deferred paid-tier meter.
   - Keep it in `client/` so it stays caller-agnostic and survives the future
     spin-out (a standalone `defimind-client` SDK would carry the same header).

   > **Companion change required in a DIFFERENT repo — flag, do not silently skip.**
   > A header the package *sends* is invisible unless the server *logs* it. The
   > `defimind-mcp` server (`/Users/ian_moore/repos/defimind-mcp`,
   > `src/defimind_mcp/server.py`) must be updated to read the incoming
   > `User-Agent` / `X-DeFiMind-Client` header and include it in its per-request log
   > line (e.g. `client=defimind-agent/0.1 tool=CheckPoolHealth`), so it surfaces in
   > **Railway's** stdout/stderr log stream where the operator can filter for it.
   > Without this server-side half, the package sends a marker nothing records and
   > Railway shows nothing. This server change is OUT OF SCOPE for the `defimind`
   > package build itself, but MUST be captured as a follow-up task against
   > `defimind-mcp` so the observability signal actually works end to end.

3. **`config/config.py`** — `load_config()` and validation. Returns a typed object
   or a validated dict. Config path resolves from CWD (`Path("config.toml")`).

4. **`modes/monitoring.py`** — the monitoring mode: given a client + config, build
   `tool_args`, call the two `MONITORING_TOOLS`, run `check_alerts`. **Wire
   `check_alerts()` to the real captured fields** from Phase 0 (this is the one real
   logic change in this phase). Keep print-first: full payload always shown, alerts
   additive. A mode should expose a clean callable (e.g. `async def
   run(client, config) -> None` or yielding report items).

5. **`orchestration/runner.py`** — thin: load config (via `config/`), construct the
   client (via `client/`), select the mode (via `agents/cleo`), run the cycle, sleep,
   retry-on-cycle-error, handle Ctrl-C. This is the `run_cycle` + `main` loop. Keep
   it small — it is a runner, not a framework.

6. **`report/report.py`** — `report_pool`-style formatting: a result + alerts →
   printed human-readable block. Isolated here because MVP-C will hook anchoring and
   MVP-B will hook rendering at this layer.

7. **`agents/cleo.py`** — the Cleo persona: the intro/voice line ("Cleo is watching
   … analysis only, you decide"), and the binding of which mode(s) run. At MVP-A this
   is thin (one mode, monitoring), but it's where "it's always Cleo, in modes" lives,
   so the seam for adding modes is here, not scattered.

8. **`cli.py`** — `run()` parses minimal args (none required beyond maybe
   `--config`), calls `orchestration.runner`. Wired as the `defimind` console script.

9. **Remove all three `[VERIFY]` comments** — the SDK surface (Phase 0) and the
   alert field-wiring (this phase) are now resolved.

10. **Confirm identical behavior.** `defimind` runs the same monitoring loop,
    produces the same reports as Phase 0, now with alerts firing on real fields.

## Minimal tests (full suite is Phase 2, but seed them here)

- `tests/test_client.py` — client constructs, parses a sample payload correctly
  (can use a captured Phase-0 payload as a fixture; no live call needed).
- `tests/test_config.py` — valid config loads; missing keys / placeholder RPC / no
  pools each fail with a clear error.
- `tests/test_modes.py` — `check_alerts` fires on a known-bad captured payload, stays
  quiet on a healthy one.

## Gate to advance to Phase 2

- [ ] Submodule tree in place; Phase-0 logic decomposed per the table.
- [ ] `client/` has **zero** outward `defimind` imports; public API is clean and
      extraction-ready; no agent/cleo vocabulary in it.
- [ ] Every outgoing request carries the identifying client header (set in
      `client/`); the companion `defimind-mcp` server-side logging change is
      recorded as a follow-up task (even if not yet done — it's a separate repo).
- [ ] **No `defipy`/web3/chain import** anywhere in the package.
- [ ] `check_alerts()` wired to real fields; fires on known-bad, quiet on healthy.
- [ ] All `[VERIFY]` comments gone.
- [ ] `defimind` command behaves identically to Phase 0 (same loop, same reports).
- [ ] Seed tests pass (`pytest`).

## Out of scope for Phase 1

- New modes beyond `monitoring` (the structure makes room; don't build them).
- The other three endpoint tools in the loop (documented as easy-to-add, not wired).
- README example, metadata polish, full test coverage (Phase 2).
- Anything paid-tier, hosted, or AR.
