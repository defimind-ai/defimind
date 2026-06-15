# Phase 0 — Package Scaffold & First Contact

*Hand-off spec for Claude Code. Part of the MVP-A `defimind`-package phase set
(`PHASES_INDEX.md`). Do this first.*

---

## Goal

Two things, in one phase, because they validate each other:
1. Stand up the **`defimind` package skeleton** (`src/` layout + `pyproject.toml`,
   mirroring `defimind-mcp`) so `pip install -e .` works and a `defimind` console
   command exists.
2. Get the **working monitoring logic running against the live endpoint** and
   **capture the real tool output** — resolving the two `[VERIFY]` unknowns carried
   over from the `cleo.py` prototype.

This phase is allowed to put the working logic in **one module first** (e.g.
`src/defimind/_app.py`, essentially the proven `cleo.py` body) — the clean
decomposition into submodules is **Phase 1**. The point of Phase 0 is: package
installs, command runs, real output captured. Structure comes next.

## Reference material (reuse, don't reinvent)

- **`/Users/ian_moore/repos/cleo/cleo.py`** — the proven logic: `load_config()`,
  `extract_payload()`, `check_alerts()` (stubbed), `tool_args()`, `report_pool()`,
  `analyze_pool()`, `run_cycle()`, `main()`. Shape is correct; reuse it wholesale as
  the Phase-0 single-module body.
- **`/Users/ian_moore/repos/cleo/config.example.toml`** — the config shape
  (`rpc_url`, `endpoint`, `poll_interval_seconds`, `[[pools]]`). Copy it.
- **`/Users/ian_moore/repos/defimind-mcp/pyproject.toml`** — the packaging
  convention to mirror (setuptools, `src/` layout, `[project.scripts]`, pinned deps,
  URLs).

## Working directory

`/Users/ian_moore/repos/defimind` (repo root; `LICENSE` already present, Apache-2.0).

## Pre-flight

- Read `cleo.py`, `cleo/config.example.toml`, and `defimind-mcp/pyproject.toml` in
  full before writing anything.
- Confirm Python **3.11+** (stdlib `tomllib`).
- Confirm the endpoint is live: `curl https://mcp.defimind.ai/health` returns ok with
  the tool list. If not, stop and flag — the endpoint is the dependency.

## Tasks

1. **Create the package skeleton** under `src/defimind/`:
   - `src/defimind/__init__.py` (version string, e.g. `__version__ = "0.1.0"`).
   - `src/defimind/_app.py` — the proven `cleo.py` logic, adapted minimally:
     config path resolves from CWD (`Path("config.toml")`) rather than next to the
     module (a packaged install has no co-located config). Keep the `[VERIFY]`
     comments for now.
   - `src/defimind/cli.py` — a `run()` that calls the app's `main()`
     (`asyncio.run(...)`), so the console script has an entry point.
   - `config.example.toml` at repo root (copy from `cleo/`).
   - `.gitignore` — at minimum `config.toml`, `.venv/`, `__pycache__/`, `*.pyc`,
     `*.egg-info/`, `build/`, `dist/`.

2. **Write `pyproject.toml`** (mirror `defimind-mcp`'s, adapted):
   ```toml
   [build-system]
   requires = ["setuptools>=68", "wheel"]
   build-backend = "setuptools.build_meta"

   [project]
   name = "defimind"
   version = "0.1.0"
   description = "DeFiMind's LP analyst agent (Cleo) — monitors Uniswap positions via the DeFiMind MCP endpoint. Analysis only."
   readme = "README.md"
   requires-python = ">=3.11"
   license = { text = "Apache-2.0" }
   authors = [{ name = "Ian C. Moore" }]
   keywords = ["defi", "uniswap", "mcp", "agent", "liquidity", "analytics", "cleo"]
   dependencies = ["mcp>=1.27.0"]      # the ONLY runtime dep. NOT defipy.

   [project.scripts]
   defimind = "defimind.cli:run"

   [project.optional-dependencies]
   dev = ["pytest>=8.0"]

   [project.urls]
   Homepage = "https://defimind.ai"
   Repository = "https://github.com/defimind-ai/defimind"
   Paper = "https://arxiv.org/abs/2605.11522"

   [tool.setuptools.packages.find]
   where = ["src"]
   ```

3. **Install it and confirm the command exists.**
   ```bash
   cd /Users/ian_moore/repos/defimind
   python -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   defimind --help     # or: defimind  (it should start and look for config.toml)
   ```
   Record the installed `mcp` version (`pip show mcp`). Confirm the
   `from mcp import ClientSession` / `from mcp.client.streamable_http import
   streamablehttp_client` imports resolve against it (`[VERIFY]` #1). If they differ,
   record the correct paths — fix them here (this is the package's real dep, so it's
   in scope to get the import right now).

4. **Create a real `config.toml`** at repo root (`cp config.example.toml
   config.toml`), set a **real** mainnet `rpc_url`, keep the example V3 pool, set a
   short `poll_interval_seconds` (e.g. 60) for testing. **Confirm `git status` never
   shows `config.toml` staged.** Do not paste the RPC URL into any doc or commit.

5. **Run it against the live endpoint.**
   ```bash
   defimind          # runs the loop; let one full cycle complete, then Ctrl-C
   ```
   It should print a header, then `CheckPoolHealth` and `DetectRugSignals` report
   blocks with full JSON payloads.

6. **Capture the real output verbatim** (the deliverable that unblocks Phase 1) —
   into a **git-ignored / operating-notes** scratch location, NOT the public repo.
   For each of `CheckPoolHealth` and `DetectRugSignals` record:
   - exact top-level keys + types;
   - for `DetectRugSignals`: how signals/flags are represented (dict of bools? list?
     score?) — this is what Phase 1 wires alerts to;
   - whether payloads arrive as `structuredContent` or JSON text (confirms
     `extract_payload`'s branch).

## Gate to advance to Phase 1

- [ ] `pip install -e ".[dev]"` succeeds; `defimind` console command exists and runs.
- [ ] `mcp` version recorded; SDK import/call surface confirmed (or corrected) —
      `[VERIFY]` #1 resolved.
- [ ] One real `CheckPoolHealth` + one real `DetectRugSignals` payload captured
      verbatim with exact field structure — `[VERIFY]` #2 *known* (wiring is Phase 1).
- [ ] `config.toml` never committed; no secret in any tracked file.

If the run errors before output, that error is the finding — capture it; it's the
first thing Phase 1 addresses.

## Out of scope for Phase 0

- Submodule decomposition (Phase 1) — one working module is fine here.
- Wiring `check_alerts()` to real fields (Phase 1).
- README example, full test suite, metadata polish (Phase 2).
- Anything paid-tier.
