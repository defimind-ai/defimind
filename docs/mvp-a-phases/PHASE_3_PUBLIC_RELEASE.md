# Phase 3 — Public Release

*Hand-off spec for Claude Code. Part of the MVP-A `defimind`-package phase set
(`PHASES_INDEX.md`). Do not start until Phase 2's gate is met — a clean-env install
must already reach a real result before going public.*

---

## Goal

Ship `defimind-ai/defimind` public: push the finished package, set discoverability
metadata, and **verify the install-to-result path works for an outside user**. This
phase ends with the free `defimind` agent genuinely live and installable.

## Pre-flight

- Phase 2 gate met (clean-env `pip install` → real result).
- `defimind-ai/defimind` already exists on GitHub (the repo whose `LICENSE` is on
  disk). Confirm the local repo's remote points at it (`git remote -v`).

## Tasks

1. **Confirm git state.**
   - `git status` — `config.toml` NOT staged; working tree as expected.
   - `git ls-files` — confirm `config.toml`, `.venv/`, `*.egg-info/`, `build/`,
     `dist/` are not tracked.
   - `git remote -v` — points at `github.com/defimind-ai/defimind`.

2. **Commit and push.**
   - `git add -A`, then **re-confirm `config.toml` is excluded** before committing
     (a pushed RPC key is a leaked secret — this is the one irreversible mistake).
   - Commit (e.g. `"defimind v0.1.0: Cleo monitoring agent (free), installable"`).
   - `git push -u origin main` (match the actual default branch).

3. **Repo metadata for discoverability** (GitHub):
   - Description, e.g. *"DeFiMind's LP analyst agent (Cleo). Monitors your Uniswap
     positions via the DeFiMind MCP endpoint. Installable, analysis-only."*
   - Topics: `defi`, `uniswap`, `mcp`, `agent`, `liquidity`, `analytics`, `ethereum`.
   - Confirm Apache-2.0 shows in GitHub's UI.
   - Confirm the README renders correctly (header/icon, example block, links, badges).

4. **Verify the public install path end-to-end** (the gate) — as an outside user,
   from a clean machine/temp dir:
   ```bash
   git clone https://github.com/defimind-ai/defimind.git
   cd defimind
   python -m venv .venv && source .venv/bin/activate
   pip install .
   cp config.example.toml config.toml
   # edit config.toml with a real RPC + a pool
   defimind
   ```
   Confirm it reaches a real result. Fix and re-push if any step fails for a fresh
   user.

5. **Secret hygiene post-push.** Browse the public repo + commit history; confirm
   `config.toml` is absent and no RPC URL / API key appears anywhere. (If a secret
   was ever committed, rotate it — public git history is permanent.)

## Gate — MVP-A (`defimind` free agent) is PUBLIC

- [ ] `defimind-ai/defimind` is a public repo: correct description, topics,
      Apache-2.0, README rendering.
- [ ] Finished package pushed; no secrets in tree or history.
- [ ] Outside-user `git clone` → `pip install .` → `defimind` → real result works,
      following only the README.

## After this phase (NOT part of it — per the plan)

- **Delete the `cleo/` prototype directory** — its logic now lives in the `defimind`
  package; it was the prototype and is superseded. (Do this once Phase 3's gate is
  confirmed, not before — it's the fallback reference until then.)
- **Pause on MVP-B / MVP-C** — do not start the hosted widget or AR convergence.
- **Brainstorm what to do with a public, installable MVP-A** — distribution, the
  first public analysis post (the real captured output is the substance), warm-audience
  outreach, a possible PyPI publish, the `defimind-client` SDK spin-out from
  `client/`. Separate working session, not a build phase.

## Out of scope for Phase 3

- PyPI publish (optional later decision; repo-install suffices for MVP-A public).
- Paid tier, hosted surface, AR — all deferred.
- Post-launch distribution work — that's the brainstorm, after the gate.
