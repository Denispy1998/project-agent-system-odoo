# Known Limitations

This document lists architectural limitations honestly, so future readers
(including the thesis jury) can distinguish *bugs* from *design trade-offs*.

---

## L1 — Permission guard: server-side verified (v2.5)

**Historically (before v2.5):** the chat orchestrator blocked write intents
for Team Members, but the underlying `odoo_tools.py` connected to Odoo with
`admin/admin` (from `.env`). Any direct HTTP call to the FastAPI service
that passed `is_manager: true` would execute writes with admin privileges.

**Current state (v2.5):** the FastAPI layer no longer trusts the client
flag. `main.py` calls `verify_user_is_manager(user_id)` which queries Odoo
via XML-RPC to confirm actual group membership. Client claims are ANDed with
server truth: an attacker sending `is_manager: true` for a Team Member is
downgraded server-side (logged as `[PermissionGuard] ... downgraded`). The
check uses a 60-second TTL cache to keep XML-RPC traffic negligible.

**Residual risk:** if an attacker has shell access to the host, they can
read `.env` and call Odoo directly as admin, bypassing both FastAPI and
the orchestrator. That case is outside the threat model of a locally-hosted
prototype.

**Why this is acceptable today:**
- FastAPI listens on `127.0.0.1:8001` only (not exposed on the LAN).
- The browser UI correctly derives `is_manager` from
  `_is_user_manager()` and sends it to the API.
- The only realistic attacker is a local process, which already has
  shell access anyway.

**What a production version would do:**
- Bind each chat request to an Odoo session (via `session_id` cookie or
  a signed token) and use XML-RPC with the user's own credentials.
- Or use Odoo's built-in `/web/dataset/call_kw` JSON-RPC with CSRF tokens.
- Alternatively, run two XML-RPC connections: `admin` for reads, the
  real user for writes.

**Impact if ignored:** none for the PIC2 scope (single-user evaluation).
Documented here for integrity.

**Related incident:** during v2.4 testing, the app-level guard missed the
`set` and `mark` verbs used by new router patterns, briefly allowing a
Team Member to write via chat. Fixed in v2.4.4. See T8 in
CHANGELOG_TECHNICAL.md — an instance of L1 propagating one layer up.

---

## L2 — No pytest suite (smoke test only)

**Status (v2.5.1):** a scripted smoke test now exists at tests/smoke_test.py. It runs 16 end-to-end checks (services, router local, diagram generation, task status tool, RBAC, server-side verification). Exit code 0 on success, 1 on failures. Pytest unit tests and CI integration remain as future work.


**Symptom:** all verification is manual (curl, browser, `odoo-bin shell`).
No pytest, no CI.

**Why:** the project grew organically from a personal dev workflow during
a hardware-loss recovery. Tests were not prioritized given the time budget.

**Partial mitigation:**
- `docs/CHANGELOG_TECHNICAL.md` records the manual verification performed
  after every change.
- The repo tags (`v2.1` … `v2.4`) enable bisecting if a regression appears.

**Impact:** manual verification takes longer than `pytest -q`, but the
project's scale (17 tools, 8 HTTP routes) keeps it tractable.

---

## L3 — No cache on `_is_user_manager`

**Symptom:** every visit to `/assistente` runs 2 SQL queries to check
group membership (one `res.groups` lookup + one `group_ids` check).

**Why it was removed:** the original `@lru_cache` version had stale-data
bugs when a user's role changed at runtime. Removing the cache was the
quickest correctness fix.

**Planned follow-up (FASE 3):** reintroduce cache with explicit
invalidation on `res.users` write (via `@api.depends` or a post-hook).

**Impact today:** ~5-10 ms per request, negligible.

---

## L4 — Filestore has orphan assets

**Symptom:** `FileNotFoundError` for 3-4 attachment hashes in `~/odoo.log`.

**Cause:** the hardware crash wiped `~/.local/share/Odoo/filestore/odoo/`
and the restore did not include every binary blob. The corresponding
`ir.attachment` records still reference non-existent files.

**Impact:** cosmetic — those specific attachments cannot be downloaded.
No user-facing feature depends on them.

**Fix if needed:** `-u web` regenerates CSS/JS assets; orphan attachment
records can be unlinked from Odoo UI (Settings → Technical → Attachments).

---

## L5 — Groq free-tier rate limits

**Symptom:** heavy use of the LLM fallback (>~20 queries in 1 min) hits
`1000 OTPM` and the chat returns a friendly retry message.

**Mitigation already in place:**
- Hybrid router handles ~90% of commands locally (no LLM call).
- Diagram intent gets a local shortcut (1 LLM call instead of 2).
- On rate limit the orchestrator waits 60 s and retries once.

**Not yet implemented:**
- Exponential backoff (30 s → 60 s → 120 s).
- Local response cache keyed by intent.

**Impact:** acceptable for the PIC2 evaluation; documented for transparency.

---

## L6 — RSL/ASL specs are documentation, not code-generated

The `docs/specs/*.rsl` and `*.asl` files (v2) are validated in ITLingoCloud
(0 errors) and describe the system faithfully. They are **not** consumed by
code generators or CI; they are the human-readable specification.

**Reason:** ITLingo's toolchain is independent of this repo, and
round-tripping from RSL to Odoo models was out of scope for the project.

---

## L8 — Docker files are reference artifacts

The docker/ folder contains a Dockerfile for the FastAPI + CrewAI microservice and a matching docker-compose.yml, but they have NOT been run end-to-end. They are provided as reference artifacts for portability discussions and future work. The primary deployment remains direct execution in WSL2 (see start_all.sh). Full containerization of Odoo 19 + PostgreSQL is listed as future work.

---

## L7 — Browser UI is server-rendered

All UI is Python f-strings inside `chatbot.py` (~1456 lines). There is no
React/Vue frontend. This keeps the deployment trivial (one Python process)
but makes HTML/CSS changes verbose.

**Impact:** acceptable; documented so future maintainers know the trade-off.
