# Thesis Material — PIC2 and Dissertation

This document consolidates raw material for the thesis chapters, extracted
from the working codebase, technical changelog, and architectural decisions
made during the project. It scaffolds the PIC2 report (15 January 2027) and
the dissertation (Semester 2, 2027).

---

## 1. Methodology (Design Science Research)

The project follows the Design Science Research (DSR) framework proposed by
Hevner et al. (2004) and refined by Peffers et al. (2007).

### 1.1 Relevance Cycle (problem context)

Modern project and product management involve multiple stakeholders,
artefacts, and distributed decisions over time. Activities such as project
planning, backlog management, execution tracking, risk management, and
reporting are still largely manual and fragmented, especially in SMEs and
research labs. Large Language Models (LLMs) can automate parts of this work
but integrating them with enterprise tools requires addressing:

- Intent classification (natural language to concrete operations)
- Role-aware permissions (project manager vs team member)
- Graceful degradation under rate limits and network failures
- Data persistence consistency across AI and enterprise systems

### 1.2 Design Cycle (artefact construction)

The artefact is an AI multi-agent ecosystem integrated with Odoo 19 via
XML-RPC. Design decisions are documented in docs/CHANGELOG_TECHNICAL.md
and docs/LIMITATIONS.md.

Key design choices:

- Hybrid Router — local regex classifier absorbs ~90% of commands in
  under 0.5 s, with zero LLM calls. Only unknown intents go to the LLM.
- XML-RPC tools — 17 idempotent tools wrapping Odoo CRUD operations.
- CrewAI agents — role-based LLM agents (Project Manager, Team Member,
  Reporting, Diagram) with short backstories to control token usage.
- RBAC at two layers — Odoo ir.model.access + orchestrator-level guard.
- Task lifecycle — project.task.task_status (In Backlog / In Progress /
  Concluded) with automatic date_end handling.
- Dynamic diagrams — the LLM generates Mermaid code, with a weighted
  keyword classifier and deterministic fallback on LLM failure.

### 1.3 Rigor Cycle (knowledge base)

The artefact draws from:

- Software Engineering: DSR (Hevner, Peffers), Domain-Specific Languages
  (ITLingo RSL/ASL from Prof. Alberto Silva s BillingSystem case study)
- AI/LLM: CrewAI 0.175.0, LiteLLM 1.74.9, prompt engineering for
  constrained outputs (Mermaid, XML-RPC payloads)
- Enterprise systems: Odoo 19 ORM, PostgreSQL 18 access control

---

## 2. Implementation

### 2.1 Architecture (v2.4.3)

Browser -> Odoo (chatbot.py) -> HTTP :8001 -> FastAPI (agents_api)
      |                                            |
  Odoo DB <- odoo_tools.py (XML-RPC)          CrewAI -> LLM (Groq)

### 2.2 Components

| Component      | File                              | Purpose                              |
|----------------|-----------------------------------|--------------------------------------|
| Odoo module    | odoo-module/                      | Web UI, chat, dashboards, RBAC, cron |
| FastAPI        | agent/agents_api/main.py          | /agent/run + /health                 |
| Orchestrator   | agent/agents/orchestrator.py      | Hybrid router + LLM fallback         |
| Router         | agent/agents/router.py            | 17 regex patterns (local, no LLM)    |
| Tools          | agent/tools/odoo_tools.py         | 17 idempotent XML-RPC tools          |
| Mermaid        | agent/tools/mermaid_tools.py      | LLM-based diagram generation         |


### 2.3 Task Lifecycle (v2.2, refined in v2.3 and v2.4.3)

Model (odoo-module/models/project_task.py):

    task_status = fields.Selection(
        selection=[("in_backlog", "In Backlog"),
                   ("in_progress", "In Progress"),
                   ("concluded", "Concluded")],
        default="in_backlog", required=True, tracking=True)

The write() override auto-fills date_end when transitioning to concluded
and clears it when moving back. This makes the KPI avg_lead_time
(= avg(date_end - create_date)) semantically meaningful.

UI (odoo-module/views/task_views.xml):
- Form: editable radio widget under Lifecycle group
- List: colored badge column
- Search: three filters (In Backlog / In Progress / Concluded)
- Project dashboard (/assistente/projeto/<id>): inline clickable
  badges that cycle the status via /assistente/task/<id>/cycle

Chat: set task <name> in <project> to <status> — accepts synonyms
(done, finished -> concluded; doing, wip -> in_progress;
todo, backlog -> in_backlog).

### 2.4 Role-Based Access Control (v2.3)

Two-level enforcement:

1. Odoo level (security/ir.model.access.csv):
   - Gestor de Projeto: RW on project.task and project.project
   - Membro de Equipa: R only
2. Orchestrator level (agents/orchestrator.py): if is_manager=False
   and intent is a write, returns DENIED: immediately (no LLM call).

The group membership check (_is_user_manager) runs on a 60 s TTL cache
and uses sudo() to bypass record rules that hide groups from non-admins.

Verified: joao (now Manager) sees write-capable chat, jose (Team
Member) sees read-only chat. Both see identical global KPIs (dashboard
uses sudo() for ecosystem-wide metrics).

### 2.5 Dynamic Mermaid Diagrams (v2.2, v2.2.1)

Input: draw a <kind> diagram of <description>

Pipeline:
1. Local intent detection — weighted keyword classifier picks one of:
   flowchart, sequence, er, class, state, gantt, pie
   (weights: 10 = explicit sequence diagram, 5 = generic process)
2. LLM call — single call to groq/qwen/qwen3.8-27b with a strict
   system prompt that requires a single fenced mermaid block
3. Deterministic fallback — if the LLM is unavailable, a minimal but
   valid diagram of the detected kind is returned

Key architectural decision (v2.2.1): the orchestrator detects diagram
intent locally and calls the tool directly, bypassing CrewAI. This
halves the LLM call count (2 -> 1) and lets the fallback work even
under rate limit.

Verified: all 7 kinds generate specific diagrams (not templates) in
0.3-1.5 s. Example: sequence diagram of login flow returned a full
sequence with alt/else blocks and JWT token generation.

---

## 3. Evaluation

### 3.1 Quantitative Metrics (as of 9 October 2026)

Measured on a local WSL2 environment (Ubuntu 26.04, Python 3.12,
PostgreSQL 18, Odoo 19). Groq free tier for LLM calls.

| Metric                        | Before v2.1  | v2.4.3       | Delta       |
|-------------------------------|--------------|--------------|-------------|
| Router local latency          | 2-5 s        | 0.1-0.2 s    | ~20x        |
| Diagram generation latency    | 2-5 s (2 LLM)| 0.3-1.5 s (1)| ~5x         |
| Rate-limit failures (per 100) | high         | ~10          | router+bkoff|
| Tools available               | 14           | 17           | +3          |
| RBAC layers                   | 1 (advisory) | 2 (enforced) | +1          |
| Task lifecycle support        | none         | full         | new         |

### 3.2 Qualitative Evaluation (case studies)

Seven instructive bugs were documented during development. Each one
corresponds to a real failure mode of integrating LLMs with enterprise
systems (see docs/CHANGELOG_TECHNICAL.md for full detail):

| ID | Title                                       | Severity |
|----|---------------------------------------------|----------|
| T1 | PostgreSQL ownership blocks upgrade         | Critical |
| T2 | flow vs sequence diagram detector bug       | High     |
| T3 | groups_id to group_ids (Odoo 19)            | High     |
| T4 | request.env hides groups from user          | High     |
| T5 | XML ID mismatch + dead groups.xml           | High     |
| T6 | Greedy regex deleted 172 lines              | Critical |
| T7 | CrewAI Tool not callable                    | Medium   |

These cases illustrate three recurring challenges:

(a) Cross-version migrations in enterprise frameworks (T1, T3, T5)
(b) LLM/agent framework quirks (T2, T7)
(c) Framework hidden state / record rules (T4) and tooling pitfalls (T6)

### 3.3 End-to-end Validations

All of the following were verified manually in the browser or via curl:

- Manager role (joao): sees Manager UI, write-capable chat
- Team Member role (jose): sees read-only UI, writes return DENIED
- Dashboard KPIs identical for both roles (7 projects, 24 tasks, 15
  stages, lead time 26.0, activity 0.9)
- Task status editable from Odoo form (radio widget) and from the
  project dashboard (inline clickable badges)
- Task status editable from chat (set task X in Y to Z)
- Diagram shortcut generates 7 kinds of Mermaid diagrams
- Weekly cron fires autonomously, sends HTML email via SMTP
- 0 errors in Odoo log and FastAPI log after a full smoke test

---

## 4. Discussion

### 4.1 Architectural Limitations (see docs/LIMITATIONS.md)

The following limitations are acknowledged honestly and framed as
trade-offs of the current scope, not as defects:

- L1 — Permission guard is advisory on the Odoo side: odoo_tools.py
  connects as admin. Mitigated by FastAPI binding to 127.0.0.1 and by
  the orchestrator guard. A production version would bind requests to
  an Odoo session.
- L2 — No automated test suite: all validation is manual (curl,
  browser, odoo-bin shell). Tractability is ensured by project scale
  (17 tools, 8 HTTP routes) and by 9 Git tags for bisecting.
- L3 — No cache on _is_user_manager (before v2.4.1): now uses a 60 s
  TTL cache, eliminating per-request SQL lookups.
- L4 — Filestore has 3-4 orphan assets from the hardware crash,
  purely cosmetic.
- L5 — Groq free-tier rate limits: mitigated by hybrid router, diagram
  shortcut, and exponential backoff (v2.4.2).
- L6 — RSL/ASL specs are documentation, not consumed by code
  generators.
- L7 — Browser UI is server-rendered (Python f-strings), simplifying
  deployment at the cost of verbosity.

### 4.2 Lessons Learned

1. Intent classification from natural language needs weighted evidence,
   not order-based heuristics (see T2).
2. Enterprise frameworks rename core fields between major versions;
   never assume Odoo APIs are stable (see T3).
3. The question does user X belong to group Y needs elevated privileges
   in Odoo (sudo), but the answer is role-independent (see T4).
4. Defensive flags like raise_if_not_found=False hide real bugs during
   development; use them only in production fallbacks (see T5).
5. Never use regex to remove code from large files. Use AST-aware tools
   or exact line numbers after grep -n (see T6).
6. Decorators can change the callable s type (CrewAI Tool not callable)
   inspect type(obj) before calling (see T7).
7. When integrating LLMs with enterprise systems, a hybrid architecture
   (local classifier + LLM fallback) is preferable to pure-LLM routing:
   it reduces latency, cost, and rate-limit exposure.

### 4.3 Contribution to the State of the Art

The project contributes:

- A reference architecture for LLM-Odoo integration using XML-RPC and
  a hybrid router that respects enterprise RBAC.
- A concrete implementation of task lifecycle tracking aligned with
  the RSL/ASL specification (v2.0, ITLingo valid, 0 errors).
- A catalogue of 7 typical integration pitfalls with reproductions and
  fixes, useful for practitioners and educators.
- A demonstration that free-tier LLM providers (Groq) can support
  production-grade features when paired with a robust local layer.

---

## 5. References (to be formatted per MEIC guidelines)

- Hevner, A. R., March, S. T., Park, J., Ram, S. (2004). Design Science
  in Information Systems Research. MIS Quarterly, 28(1), 75-105.
- Peffers, K., Tuunanen, T., Rothenberger, M. A., Chatterjee, S. (2007).
  A Design Science Research Methodology for Information Systems Research.
  Journal of MIS, 24(3), 45-77.
- Silva, A. R. (2024). ITLingo DSL framework — RSL and ASL specification
  languages. Case-study methodology (BillingSystem).
- CrewAI Documentation. https://docs.crewai.com (v0.175.0)
- Odoo 19 Developer Documentation. https://www.odoo.com/documentation/19.0
- LiteLLM Documentation. https://docs.litellm.ai
- Groq API Reference. https://console.groq.com/docs
- PostgreSQL 18 Documentation. https://www.postgresql.org/docs/18/

---

## Appendix A — Repository Structure (v2.4.3)

    project-agent-system-odoo/
    |-- agent/                    # FastAPI + CrewAI microservice
    |   |-- agents/               # orchestrator, router, 4 agents
    |   |-- agents_api/           # FastAPI main + requirements
    |   |-- tools/                # odoo_tools + mermaid_tools
    |   `-- setup_users.py
    |-- odoo-module/              # meu_assistente_ia module
    |   |-- controllers/          # chatbot, dashboard_utils, sessions
    |   |-- models/               # ai_session, project_task, project_project
    |   |-- views/                # menu, task_views
    |   |-- security/             # groups, ir.model.access
    |   `-- data/                 # ir_cron_data
    |-- docs/
    |   |-- specs/                # RSL/ASL v2 + diagrams
    |   |-- CHANGELOG_TECHNICAL.md
    |   |-- LIMITATIONS.md
    |   `-- THESIS_MATERIAL.md    # this file
    |-- .env.example
    `-- README.md

## Appendix B — Git Tags

    v2.1     restore stage_id=False for new tasks
    v2.2     task_status + dynamic Mermaid - deep thinking
    v2.2.1   list_tasks without project + diagram shortcut
    v2.3     RBAC + task views + dashboard consistency
    v2.4     set_task_status tool + router patterns
    v2.4.1   role TTL cache
    v2.4.2   exponential backoff
    v2.4.3   inline status cycle buttons

