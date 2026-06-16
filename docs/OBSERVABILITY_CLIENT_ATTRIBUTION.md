# Client Attribution & Observability — shared spec

*Cross-cutting hand-off spec for Claude Code. Not part of any single MVP phase set —
it spans **MVP-A** (the `defimind` package / Cleo), **MVP-B** (the hosted widget),
and the **`defimind-mcp` server** (which does the actual logging). Build the
server-side half once; each client surface sends its own marker.*

*Captured: June 14, 2026.*

---

## What this is for

The DeFiMind MCP endpoint (`mcp.defimind.ai`) is **authless**, so by default every
incoming call looks identical on the wire — a call from the `defimind` package, the
hosted widget, Claude Desktop, Cursor, or `curl` are indistinguishable. This spec
adds a **rough, free client-attribution signal** so that, in **Railway logs**, you
can tell *which surface* traffic is coming from:

- traffic from the **`defimind` package (Cleo)** — the installed dev agent (MVP-A)
- traffic from the **hosted widget** — the metered non-dev surface (MVP-B)
- everything else (generic MCP clients) — untagged

This is the usage signal that lets you watch demand and **gate (= meter) when cost
justifies it.** It is the instrument behind "monitor endpoint cost, gate if it gets
out of control."

## What this is NOT (read this — it sets the honest expectations)

- **Not authentication.** A header is trivially spoofable. Anyone can send the same
  string. This tells you what callers *identify as*, not what they provably are.
- **Not per-user.** All package traffic carries the same `cleo` marker; all widget
  traffic carries the same `widget` marker. It distinguishes *surfaces*, not
  *individual users*. ("Which user, how do I bill them" is the deferred paid-tier
  meter — the `hash(key)` ledger — not this.)
- **Not a security boundary.** Do not gate, authorize, or trust anything based on
  this header. It is observability only.

If precise or trustworthy attribution is ever needed, that's the paid-tier credit
key, not this. This is a cheap "roughly how much of my traffic is which surface"
signal, and that's all.

---

## Design — one marker scheme, two clients, one server change

### The marker

Every call from a DeFiMind-built client sets an HTTP header identifying the surface
and version. Use a custom header so it doesn't collide with the SDK's own
`User-Agent` handling:

```
X-DeFiMind-Client: cleo/<pkg-version>      # from the defimind package (MVP-A)
X-DeFiMind-Client: widget/<widget-version> # from the hosted widget (MVP-B)
```

(If setting a custom header isn't cleanly supported by the MCP client transport in
the installed SDK, fall back to appending the same token to the `User-Agent`, e.g.
`User-Agent: defimind-cleo/<ver>`. Either works; the server reads whichever is set.)

### Client half A — `defimind` package (MVP-A)

- Set `X-DeFiMind-Client: cleo/<__version__>` on **every outgoing request**.
- Do it in the **`client/` submodule** — it's the single chokepoint every call flows
  through, so one change tags all package traffic, automatically, for all modes.
- Pull the version from `defimind.__version__` so the marker tracks releases.
- This does **not** violate `client/`'s spin-out rule: setting a header is
  transport-level and self-contained. If `client/` is ever extracted as
  `defimind-client`, it carries its own default marker (or accepts one as a
  constructor arg) — fine either way.

### Client half B — hosted widget (MVP-B)

- The widget runs Cleo **server-side** (DeFiMind's infra + RPC). Whatever code makes
  the endpoint calls there sets `X-DeFiMind-Client: widget/<ver>`.
- Because the widget reuses the `defimind` package as its engine, the cleanest
  implementation is: the package's `client/` accepts an **optional client-marker
  override** (default `cleo/<ver>`), and the widget passes `widget/<ver>`. One code
  path, two markers, set by the caller.

### Server half — `defimind-mcp` (the part that makes it visible in Railway)

**This is the half that actually surfaces the signal — without it, clients send a
marker that nothing records.** Separate repo: `/Users/ian_moore/repos/defimind-mcp`.

- On each tool call, read the `X-DeFiMind-Client` header (and/or `User-Agent`).
- Include it in the per-request **log line** written to stdout/stderr, e.g.:
  ```
  call tool=CheckPoolHealth client=cleo/0.1.0 pool=0x88e6...5640
  ```
  (Railway shows stdout/stderr — the printed line is what you grep/filter for.)
- Default to `client=unknown` (or the raw `User-Agent`) when the header is absent,
  so untagged/generic-client traffic is still counted, just unattributed.
- **Privacy:** do **not** log the caller's `rpc_url` or any secret — the endpoint's
  whole promise is that nothing is stored/leaked. Log the client marker, the tool
  name, and non-sensitive call metadata only. Never the RPC URL.

---

## How you'll use it (Railway)

- Filter Railway logs for `client=cleo` → package/agent traffic (MVP-A signal).
- Filter for `client=widget` → hosted-widget traffic (MVP-B signal — the metered
  surface; this is the volume that maps to cost/revenue).
- `client=unknown` → generic MCP clients (Claude Desktop, Cursor, curl, etc.).
- Aggregate volume + Railway cost together = the "is it being used / is cost climbing"
  signal that triggers the decision to lay the meter.

> Reminder: traffic that goes through the **Smithery gateway** shows on Smithery's
> dashboard; traffic hitting `mcp.defimind.ai` **directly** (which is what the package
> and widget do by default) shows in **Railway**, not Smithery. This spec instruments
> the Railway-visible (direct) path.

---

## Build sequencing

- **Server half** can be built any time (it's additive logging; harmless before any
  client sends the header). Natural to do alongside the next `defimind-mcp` touch.
- **Package marker (half A)** → build with / right after the `defimind` package's
  `client/` submodule exists. (If MVP-A is already built, this is a small follow-on
  change to `client/`, not a phase edit.)
- **Widget marker (half B)** → build as part of MVP-B, reusing the package's
  optional-marker hook.

All three are small. The only ordering rule: the **server half must exist** for any
client marker to be visible — build it first or alongside, not after.

## Out of scope

- Per-user attribution / billing → deferred paid-tier credit key (`hash(key)` ledger).
- Any gating/authorization on the header → it's observability only, never a boundary.
- Logging anything sensitive (RPC URLs, keys) → never.
