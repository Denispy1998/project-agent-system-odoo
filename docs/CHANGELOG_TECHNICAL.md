# Technical Changelog — Cases Worth Documenting

This file records bugs that were instructive to debug, in enough detail
to be reused in the thesis (Discussion / Lessons Learned section).

---

## T1 — PostgreSQL ownership blocks Odoo module upgrade

**Symptom:** after restoring the Odoo DB from pg_dump executed as the
postgres OS user, running `odoo-bin -u meu_assistente_ia` failed with
`psycopg2.errors.InsufficientPrivilege: must be owner of table project_task`.

**Root cause:** pg_dump preserves ownership. The DB was restored with
`sudo -u postgres psql odoo < dump.sql`, so every table belonged to the
postgres role. Odoo connects as denispy and cannot ALTER TABLE.

**Fix:** transfer ownership of every object in the public schema to denispy.
297 tables reassigned; upgrade then succeeded.

**Lesson:** whenever you restore a dump to a different environment, plan
an ownership pass before running Odoo migrations.

---

## T2 — Naive keyword detection: flow vs sequence diagram

**Symptom:** asking the diagram tool for
"sequence diagram of the login flow between user and server" produced
a flowchart, not a sequence diagram.

**Root cause:** the local keyword detector used a first-match-wins
strategy over a list where "flow" (flowchart) appeared before
"sequence diagram". The phrase "login flow" thus hijacked the intent.

**Fix:** replaced by weighted scoring — each keyword has a specificity
weight (10 = explicit, 4 = generic), and the highest total wins.
"sequence diagram ... login flow" -> 10 (sequence) vs 5 (flowchart) -> sequence.

**Lesson:** intent classification from natural language needs weighted
evidence, not order-based heuristics.

---

## T3 — Odoo 19 renamed res.users.groups_id to group_ids

**Symptom:** the ORM shell script crashed with
`AttributeError: 'res.users' object has no attribute 'groups_id'`.

**Cause:** Odoo 19 renamed the field. res.users now uses group_ids
(elsewhere in the ORM the field stayed groups_id).

**Fix:** update all lookups in _is_user_manager and in migration scripts.

**Lesson:** Odoo does rename core fields between major versions; always
check the ORM signature before writing cross-version code.

---

## T4 — request.env does not see groups without sudo()

**Symptom:** after adding user joao to the Gestor de Projeto group,
the UI still showed him as Team Member.

**Cause:** _is_user_manager() searched res.groups through request.env,
which inherits the user's own record rules. Odoo hides groups that the
user cannot administer, so joao could not see the very group he belongs to.

**Fix:** sudo() the lookups only (the check), not the result:
`user = request.env['res.users'].sudo().browse(user_id)`
`grp = request.env['res.groups'].sudo().search([('name', '=', 'Gestor de Projeto')])`

**Lesson:** the question "does user X belong to group Y" needs elevated
privileges; the answer is role-independent.

---

## T5 — XML ID mismatch silently ignored by raise_if_not_found=False

**Symptom:** the group Gestor de Projeto existed in security/groups.xml,
but was never created in the DB.

**Double root cause:**
1. security/groups.xml was not in __manifest__.py — the file was dead code.
2. Even after adding it, the code looked up group_project_manager
   while the XML defined group_gestor_projeto. The flag
   raise_if_not_found=False swallowed the error.

**Fix:** align XML IDs and register the file. Also, remove
raise_if_not_found=False during development so misconfigurations are loud.

**Lesson:** defensive flags hide real bugs during development. Use them
only in production fallbacks.

---

## T6 — Greedy regex deleted 172 lines instead of 6

**Symptom:** a script that was supposed to remove a 4-line function
(_get_user_role_label) deleted 172 lines — including the entire
SHARED_CSS constant used by every HTML page.

**Root cause:** a non-greedy regex with a lookahead meant to stop at
the next top-level definition. Since the file has @http.route decorators
indented by 4 spaces (inside a class), the lookahead never matched; the
regex continued until the end of the file.

**Fix:** restoration from backup + surgical `sed -i '73,78d'`.

**Lesson:** never use regex to remove code from large files. Use
AST-aware tools (rope, redbaron) or exact line numbers after inspecting
with grep -n.

---

## T7 — CrewAI @tool decorates functions into Tool objects

**Symptom:** `generate_mermaid_diagram("...")` raised
`TypeError: 'Tool' object is not callable`.

**Cause:** in CrewAI 0.175.0, @tool("name") wraps the function into a
Tool instance. Calling the name directly no longer works.

**Fix:** inside the orchestrator, call .func() explicitly:
`generate_mermaid_diagram.func(description=user_message)`

**Lesson:** decorators can change the callable's type. When in doubt,
inspect type(obj) before calling.

---

## T8 — Permission guard out of sync with router write verbs

**Symptom:** a Team Member (jose) sent `set task Task-1 to concluded` via chat
and the operation succeeded instead of returning DENIED. The same happened
with `mark task X as done`.

**Root cause:** the orchestrator guard kept a hardcoded list of write verbs:

    write_keywords = ["create", "add", "delete", "remove", "move",
                      "update", "edit", ...]

When `set_task_status` was added in v2.4, its router patterns start with
`set task ...` and `mark task ...`. Neither verb was in the guard list, so
the request skipped the DENIED check and reached the tool.

**Fix:** extend the list with the router verbs (set, mark, assign) and add
a synchronization comment:

    # KEEP IN SYNC with the write verbs used by router.py patterns.

**Lesson:** when a router pattern introduces a new verb, the app-level guard
must be updated in the same change. A single source of truth (shared enum)
would prevent this class of bugs. Structural risk acknowledged in
docs/LIMITATIONS.md (L1).

---

## T9 — Client-claimed is_manager trusted at the API boundary

**Symptom:** a Team Member could execute writes by POSTing directly to
the FastAPI `/agent/run` endpoint with `is_manager: true` in the JSON
payload. The chat UI already gated writes correctly, but the API was
open to any client that could reach `127.0.0.1:8001`.

**Root cause:** the Pydantic model trusted the flag and forwarded it to
the orchestrator without verification:

    class ChatRequest(BaseModel):
        is_manager: bool = False  # client-supplied

**Fix (v2.5):** add `verify_user_is_manager(user_id)` in
`tools/odoo_tools.py`, using XML-RPC to query Odoo for real group
membership. The FastAPI layer now ANDs the client flag with the server
truth and downgrades if they disagree. Result cached for 60 s (module
TTL dict, same pattern as the Odoo-side `_ROLE_CACHE`).

**Iteration during fix:** first version failed because
`_call("res.users", "read", [[user_id], {"fields": [...]}])` passed
`fields` as a positional arg instead of a kwarg, so Odoo interpreted
the dict as another field name and raised `Invalid field fields`.
Corrected to `_call(..., [[user_id]], {"fields": [...]})`.

**Lesson:** any input that crosses a trust boundary (client -> server)
must be re-validated server-side. ANDing client claim with server truth
is safer than trusting either alone.

---

## Summary table

| ID | Title                                       | Severity | Time to fix |
|----|---------------------------------------------|----------|-------------|
| T1 | PostgreSQL ownership blocks upgrade         | Critical | ~10 min     |
| T2 | flow vs sequence diagram detector bug       | High     | ~15 min     |
| T3 | groups_id to group_ids (Odoo 19)            | High     | ~5 min      |
| T4 | request.env hides groups from user          | High     | ~10 min     |
| T5 | XML ID mismatch + dead groups.xml           | High     | ~20 min     |
| T6 | Greedy regex deleted 172 lines              | Critical | ~15 min     |
| T7 | CrewAI Tool not callable                    | Medium   | ~5 min      |
| T8 | Permission guard out of sync with router    | High     | ~10 min     |
| T9 | Client-claimed is_manager trusted at API    | Critical | ~45 min     |

**Total debug time:** ~80 min spread over one working day.
