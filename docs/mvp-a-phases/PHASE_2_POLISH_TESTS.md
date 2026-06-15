# Phase 2 — Package Polish & Tests

*Hand-off spec for Claude Code. Part of the MVP-A `defimind`-package phase set
(`PHASES_INDEX.md`). Do not start until Phase 1's gate is met.*

---

## Goal

Take the decomposed, working package to release quality: a real README example, a
proper test suite (offline + optional live gate, mirroring `defimind-mcp`), complete
`pyproject.toml` metadata, config hygiene, and the Cleo icon. No behavior changes —
this is presentation, testing, and packaging polish.

## Working directory

`/Users/ian_moore/repos/defimind`

## Tasks

1. **README (the package README already drafted alongside these phases —
   finalize it).** Confirm/complete:
   - Install via pip (from the repo now; PyPI later if/when published).
   - The `defimind` console command usage.
   - A **real** captured example-output block (from a real cycle in Phase 1) under
     a "What you'll see" section — proof it works. No real RPC URL in it.
   - The config story (`cp config.example.toml config.toml`, set RPC + pools).
   - The "analysis only — you decide" scope boundary, stated clearly.
   - The correct arrow: powered by the DeFiMind MCP endpoint; built on DeFiPy /
     State Twins. Cleo is the persona; `defimind` is the package.
   - Links resolve: `mcp.defimind.ai`, `defipy.org`, `defimind.ai`, and the State
     Twins arXiv link — **confirm the arXiv ID `2605.11522` resolves** to the real
     paper; fix if not.
   - Badges consistent with `defimind-mcp`'s style (License, Python, arXiv) if used.

2. **Test suite (mirror `defimind-mcp`'s split).**
   - **Offline tests** (no network): client payload parsing against captured
     fixtures; config validation (valid / missing-key / placeholder-RPC / no-pools);
     `check_alerts` on known-bad vs healthy fixtures; mode wiring.
   - **Optional live gate** (mirrors `defimind-mcp/tests/test_live.py`): gated behind
     an env var (e.g. `DEFIMIND_TEST_RPC_URL`), hits the live endpoint with a real
     pool, confirms a real cycle completes. Skipped when the env var is absent so the
     default `pytest` run is offline and deterministic.
   - `pytest` (offline) must be green.

3. **`pyproject.toml` metadata complete** — description, keywords, authors, URLs
   (Homepage/Repository/Paper), `requires-python`, license, console script, dev
   extra. Confirm `pip install -e ".[dev]"` and a clean `pip install .` both work.

4. **Config hygiene.**
   - `config.example.toml` is the committed template; `config.toml` is git-ignored
     and untracked (`git status`, `git ls-files`).
   - `.gitignore` covers `config.toml`, `.venv/`, `__pycache__/`, `*.pyc`,
     `*.egg-info/`, `build/`, `dist/`.
   - Remove any scratch files from Phases 0–1.

5. **Cleo icon.** Reuse the icon from the `cleo/` prototype
   (`/Users/ian_moore/repos/cleo/assets/cleo_icon.png` — the canonical one the cleo
   README referenced). Copy it into `defimind` (e.g. `assets/cleo_icon.png`), and add
   it to the README header (the float-left layout that was tuned in the prototype
   renders cleanly on GitHub's light theme). Do **not** copy the unused
   `cleo_icon0..6.png` alternates.

6. **Voice/consistency pass.** Everything reads `defimind` (package) + `Cleo`
   (persona). Entry point is `defimind`. Tone is the calm-analyst voice. Grep for
   stray `clio`/`Clio` and any leftover prototype references.

7. **Clean-env dry run (the real test of this phase).** In a fresh venv / temp dir,
   `pip install` the package from the repo, `cp config.example.toml config.toml`, set
   a real RPC, run `defimind`, confirm a real result — following only the README.
   Time it; fix the README, not your memory, if anything is unclear.

## Gate to advance to Phase 3

- [ ] README has a **real** example-output block; all links resolve (arXiv confirmed).
- [ ] `pytest` (offline) green; optional live gate present and correctly skipped
      without the env var.
- [ ] `pyproject.toml` metadata complete; clean `pip install .` works.
- [ ] `config.toml` untracked; `.gitignore` complete; no scratch files.
- [ ] Cleo icon in place and rendering; no unused alternates copied.
- [ ] No `clio` stragglers; `defimind`/`Cleo` consistent throughout.
- [ ] Clean-env `pip install` → real result in a few minutes following only the README.

## Out of scope for Phase 2

- GitHub push / public release (Phase 3).
- New modes, new tools, paid tier, hosted surface, AR.
- Publishing to PyPI (a later decision; repo-install is sufficient for MVP-A public).
