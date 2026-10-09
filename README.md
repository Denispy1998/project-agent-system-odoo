# Project Agent System — Odoo Multi-Agent AI Ecosystem

**Version 2.5.3** (RBAC + task lifecycle + Burndown/Velocity)

[![Lint](https://github.com/Denispy1998/project-agent-system-odoo/actions/workflows/lint.yml/badge.svg)](https://github.com/Denispy1998/project-agent-system-odoo/actions/workflows/lint.yml)
**Author:** Denilson Fragoso Da Silva Santos
**Institution:** Instituto Superior Técnico, University of Lisbon
**Course:** MEIC — Mestrado em Engenharia Informática e de Computadores
**Year:** 2026/2027

---

## Overview

An AI multi-agent ecosystem integrated with Odoo 19 for project management. It provides a chatbot, dashboards, weekly automated reports, and role-based permissions for Managers and Team Members.

The system uses CrewAI agents orchestrated through a FastAPI microservice, communicating with Odoo via XML-RPC. The default LLM is `groq/qwen/qwen3.8-27b` (`max_tokens=512`), with optional support for OpenAI and Anthropic models. When the LLM rate limit is hit, the orchestrator recovers the last executed tool output so idempotent write operations are never lost.

---

## Architecture

```
Browser -> Odoo (chatbot.py) -> HTTP :8001 -> FastAPI (agents_api)
       |                                            |
   Odoo DB <- odoo_tools.py (XML-RPC)          CrewAI -> LLM (Groq)
```

### Components

- **Odoo 19 module `meu_assistente_ia`**: web UI, chat sessions, dashboards, PDF/CSV export, permissions, cron.
- **FastAPI microservice** (`agents_api`): exposes `/agent/run` and `/health`.
- **CrewAI orchestrator**: routes requests to specialized agents (Project Manager, Team Member, Reporting, Diagram).
- **Odoo tools** (`odoo_tools.py`): 14 idempotent read/write tools via XML-RPC.
- **LLM**: Groq (default), optional OpenAI / Anthropic.

---

## Features

- **Hybrid Router**: local regex classifier handles ~90% of commands in
  under 0.5 s, with zero LLM calls and zero rate-limit consumption;
  unknown intents fall back to CrewAI → LLM
- **Dynamic Mermaid diagrams**: the LLM generates the diagram body
  (flowchart, sequence, ER, class, state, Gantt, pie) with a weighted
  keyword classifier for kind detection and a deterministic fallback
  on LLM failure
- **Role-based access**: *Gestor de Projeto* (RW) vs *Membro de Equipa*
  (R-only) enforced both at the Odoo `ir.model.access` layer and at the
  chat orchestrator level
- **Task lifecycle**: `project.task.task_status` (In Backlog / In Progress /
  Concluded); setting it to *Concluded* auto-fills `date_end`, reverting
  clears it. Editable via:
  * Odoo form (radio widget, tracks changes in the chatter)
  * Chat: `set task <name> in <project> to <status>`
- **17 idempotent tools** (was 14), including `set_task_status` with
  natural-language synonyms (done/finished → concluded, doing/wip →
  in_progress, todo/backlog → in_backlog)
- **Dashboard KPIs**: Lead Time (avg days for concluded tasks) and
  Activity (tasks updated in the last 7 days)
- Multi-session chat with context (`ai.session`)
- Model selector (Groq, optional OpenAI/Anthropic)
- Role-based permissions: **Manager** (read/write) vs **Team Member** (read-only)
- Global dashboard with Chart.js and per-project sub-dashboards
- PDF report with branding and risk analysis
- CSV export (semicolon separator `;`)
- 17 idempotent tools (read + write)
- Weekly AI Ecosystem Report via cron and SMTP
- Copyright footer on all pages
- Multi-language ready (English labels)

---

## Tech Stack

- Python 3.12
- Odoo Community 19
- PostgreSQL 18
- FastAPI + Uvicorn
- CrewAI 0.175.0
- LangChain 0.3.27
- LiteLLM 1.74.9
- LLM: `groq/qwen/qwen3.8-27b` (default, `max_tokens=512`)
- Agents: `max_iter=1` + `max_rpm=10` per agent (avoids retry storms on rate limits)
- Chart.js
- ReportLab

---

## Repository Structure

```
.
|-- agent/
|   |-- agents/               # CrewAI agents and orchestrator
|   |-- agents_api/           # FastAPI microservice
|   |-- config/
|   |-- tools/                # Odoo XML-RPC tools
|   `-- setup_users.py
|-- odoo-module/              # Odoo module meu_assistente_ia
|   |-- controllers/
|   |-- data/
|   |-- models/
|   |-- security/
|   |-- static/
|   `-- views/
|-- docker/                 # Reference Dockerfiles (not tested end-to-end)
|-- docs/
|   `-- specs/                # RSL/ASL specifications and diagrams
|-- .env.example
|-- LICENSE
`-- README.md
```

---

## Prerequisites

- Odoo 19 installed and running
- PostgreSQL 18
- Python 3.12
- Groq API key (or OpenAI/Anthropic)
- Odoo database with `project` module installed

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Denispy1998/project-agent-system-odoo.git
cd project-agent-system-odoo
```

### 2. Create virtual environment

```bash
python3.12 -m venv venv_agents
source venv_agents/bin/activate
pip install -r agent/agents_api/requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
nano .env
```

Required variables:

```env
GROQ_API_KEY=your_groq_key_here
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USER=admin
ODOO_PASSWORD=admin
DEFAULT_MODEL=groq
```

Optional:

```env
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

### 4. Install Odoo module

- Copy `odoo-module/` to your Odoo addons path, e.g.:

  ```bash
  cp -r odoo-module/ /opt/odoo/odoo19/addons/meu_assistente_ia
  ```

- Restart Odoo and update the module list.
- Install **Meu Assistente IA**.

### 5. Start FastAPI microservice

```bash
cd agent
uvicorn agents_api.main:app --host 127.0.0.1 --port 8001
```

Or use the provided scripts if available:

```bash
bash ~/start_all.sh
```

---

## Usage

- Open Odoo: `http://localhost:8069/assistente`
- Chat with the AI assistant, select model, manage sessions.
- View global dashboard, projects, tasks, risks.
- Export PDF/CSV reports.
- Managers can create/update/delete; Team Members are read-only.

---

## API Endpoints

### Health check

```http
GET /health
```

Response:

```json
{"status":"ok"}
```

### Run agent

```http
POST /agent/run
Content-Type: application/json
```

Payload:

```json
{
  "message": "list all projects",
  "user_id": 1,
  "is_manager": true,
  "model_name": "groq"
}
```

---

## Agent Tools (17 idempotent)

**Read (6):**

- `list_projects`
- `list_tasks`
- `list_stages`
- `analyze_risks`
- `prioritize_tasks`
- `project_summary`

**Write (10):**

- `create_project`
- `add_task`
- `create_stage`
- `move_single_task`
- `move_tasks`
- `move_all_tasks`
- `set_task_status`
- `delete_task`
- `delete_stage`
- `delete_project`

**Diagram (1):**

- `generate_mermaid_diagram` (7 kinds: flowchart, sequence, er, class,
  state, gantt, pie — dynamic via LLM with deterministic fallback)

---

## Permissions

- **Manager:** full read/write access.
- **Team Member:** read-only. Write attempts return `DENIED: ...`.

---

## Weekly Report

A cron job named **Weekly AI Ecosystem Report** generates and emails a report every week.
Configure SMTP in Odoo **Outgoing Mail Server**.
Recipient and sender are stored via `ir.config_parameter`.

---

## RSL/ASL Specifications

Located in `docs/specs/`.
Validated in ITLingoCloud with **0 errors**, following the structure of the
BillingSystem case study provided by Prof. Alberto Rodrigues da Silva.

Files:

- `AIProjectManagementAI-RSL.rsl` — Requirements Specification (v2.0)
- `AIProjectManagementAI-ASL.asl` — Application Specification (v2.0)
- `ProjectManagementAI-CaseStudy-Definition-v1.0.{md,pdf}` — informal case study
- `diagrams/` — 3 SVGs (use-case + 2 domain models)

Model coverage: Person, Project, PersonProject, ProjectStage, Task,
ChatFolder, ChatSession, StreamChat, AgentTemplate, AgentInstance, AgentTask.

---

## Known Limitations

- ITOI validator and templating engine accept different syntactic profiles.
- Groq rate limit: 1000 OTPM (output), 7000 ITPM (input) on free tier. The orchestrator handles this gracefully: the hybrid router absorbs ~90% of traffic locally, and the LLM fallback retries up to 3 times with exponential backoff [30s, 60s, 120s]. If all attempts fail, the user gets a friendly retry message instead of a raw traceback.
- Odoo 19 `ir.cron` removed `numbercall` and `doall`.
- `project.task.user_id` does not exist; use `user_ids` or `create_uid`.
- ReportLab `Bullet` style name conflict; use unique names.

---

## Graceful Degradation

The orchestrator implements a best-effort fallback strategy for LLM failures
(rate limits, empty responses, network errors) that is critical on Groq's
free tier:

- **Write intents** (`create`, `add`, `delete`, `move`, `update`) execute
  exactly **one attempt**. The tools are idempotent, so re-running them
  would waste input tokens without changing the outcome.
- **On rate limit or empty response**, the orchestrator extracts the last
  tool output from the partially executed Crew and returns it to the user.
  A write that reached the database is therefore never reported as failed.
- **If no tool output is available**, the user gets a friendly message
  (`"Rate limit reached on Groq free tier. Please retry in 60 seconds."`)
  instead of a Python traceback.

This behaviour was validated end-to-end: a `create_project` call that hit
`ITPM 7000` still persisted the project in Odoo (id 18), and the user
received a clear retry hint rather than a stack trace.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Author

**Denilson Fragoso Da Silva Santos**
Instituto Superior Técnico, University of Lisbon
MEIC 2026/2027

© Denilson Fragoso Da Silva Santos · Instituto Superior Técnico · 2026
