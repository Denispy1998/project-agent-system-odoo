# AI Project Management Ecosystem — Case Study Definition

**Version:** 1.0
**Author:** Denilson Fragoso Da Silva Santos (IST-1113142)
**Institution:** Instituto Superior Técnico, University of Lisbon
**Supervisor:** Prof. Alberto Rodrigues da Silva
**Date:** 2026

---

## 1. Overview

The **AI Project Management Ecosystem** is a web-based platform that augments
traditional project management with a multi-agent artificial intelligence
ecosystem. It integrates with the Odoo 19 platform and provides project
managers and team members with a natural-language chat interface, interactive
dashboards, and automated reporting.

The system is designed for small to medium-sized organizations that manage
multiple software projects in parallel. It addresses two main needs:

1. **Reduce the friction of routine project management** — creating projects,
   adding tasks, moving tasks between stages, and deleting obsolete items —
   by allowing users to perform these operations through natural language.
2. **Automate periodic reporting** — weekly status reports summarizing all
   projects, tasks, risks, and progress — delivering them to project managers
   without manual effort.

The platform combines a **multi-agent AI orchestrator** (which routes user
requests to specialized AI agents) with **role-based access control**
(differentiating project managers from team members) and **persistent chat
sessions** (allowing users to resume conversations across days and switch
between large language model providers).

---

## 2. Purpose and Scope

The system SHALL allow users to:

- Interact with the ecosystem through a **natural language chat interface**.
- Maintain **multiple persistent chat sessions** per user, each preserving the
  full conversation history.
- **Select the AI model provider** (Groq, OpenAI, Anthropic) for each chat
  session.
- Perform **read operations**: list projects, list tasks, list stages,
  analyze risks, prioritize tasks, and generate project summaries.
- Perform **write operations** (project managers only): create projects, add
  tasks, create stages, move tasks between stages, delete tasks, delete
  stages, and delete projects.
- Visualize **global and per-project dashboards** with interactive charts.
- Export **PDF reports and CSV files** per project.
- **Automatically generate and deliver** a weekly ecosystem report.

The system integrates with the **Odoo 19 platform** as the source of truth for
project and task data, and uses a separate **AI microservice** (built on the
CrewAI framework) to orchestrate the specialized AI agents.

---

## 3. Stakeholders

The following stakeholders have an interest in the AI Project Management
Ecosystem:

- **Project Managers** — primary users who plan, execute and monitor projects.
  They require full write access to the ecosystem, including the ability to
  create, modify and delete projects, tasks and stages.

- **Team Members** — users who contribute to projects and need visibility
  over their assigned tasks, stages and risks. They require read-only access
  to the ecosystem and cannot modify any data.

- **Product Managers** — users focused on the product backlog and
  prioritization. They consume dashboards and prioritize tasks but do not
  manage day-to-day execution.

- **System Administrators** — users responsible for configuring the ecosystem,
  managing users, monitoring the AI microservice, and configuring automated
  reports.

- **The Organization** — the entity that owns the projects and benefits from
  reduced management overhead and automated reporting.

---

## 4. Functional Description

### 4.1 Project Management

The system provides functionality to:

- Create a new project with a name and an optional list of initial tasks.
- List all existing projects, showing each project's name and task count.
- Delete an existing project together with all its associated tasks.
- View a per-project dashboard with tasks, stages, contributors, and
  interactive charts.

### 4.2 Task Management

The system provides functionality to:

- Add a new task to an existing project, initially placed in a "no stage"
  state.
- List all tasks of a project, showing each task's name and current stage.
- Move one or more tasks to a target stage within the same project.
- Delete one or more tasks from a project.
- Prioritize tasks, placing tasks without a stage first.

### 4.3 Stage Management

The system provides functionality to:

- Create a new stage inside a project, with an associated ordering sequence.
- List all stages of a project.
- Delete a stage, subject to the constraint that the stage must not contain
  any task.

### 4.4 Multi-Agent AI Chat

The system provides functionality to:

- Open a natural-language chat interface and interact with a specialized
  AI agent.
- Create multiple chat sessions per user, each with a distinct name and
  independent conversation history.
- Switch between available large language model providers per session.
- Route each user message to the most appropriate specialized agent:
  a Project Manager agent, a Team Member agent, a Reporting agent, or a
  Diagram agent.
- Analyze project risks automatically when requested, based on the number
  of tasks without an assigned stage.

### 4.5 Dashboards and Reporting

The system provides functionality to:

- Present a global dashboard with summary indicators (total projects, total
  tasks, total stages, average lead time, tasks per day).
- Display interactive charts: tasks by stage (donut), tasks by creator (bar),
  and detailed breakdowns by stage and by creator.
- Present a per-project sub-dashboard with tasks, stages, contributors and
  two charts (tasks by stage and tasks by assignee).

### 4.6 Automated Weekly Reports

The system provides functionality to:

- Automatically generate a weekly status report at a scheduled interval
  (every one week).
- Include in the report the total number of projects, total number of tasks,
  and a per-project breakdown with task count, tasks without stage, and
  estimated risk level.
- Deliver the report through the platform's internal email system.

### 4.7 Role-Based Access Control

The system provides functionality to:

- Identify whether the current user belongs to the "Project Manager" group
  (full access) or the "Team Member" group (read-only access).
- Restrict all write operations (create, add, delete, move, update) to users
  in the "Project Manager" group.
- Deny write requests issued by team members with an explicit refusal
  message.
- Display a role badge and a role-specific home page for each user.

---

## 5. Business Rules

The following business rules govern the system's behavior:

1. A **stage** cannot be deleted while it contains at least one task.
2. A **project** deletion cascades to all its tasks.
3. A **task** is initially created without an assigned stage and can be moved
   to any stage of the same project.
4. All write operations are **idempotent**: repeating the same command yields
   the same result without creating duplicates.
5. A **chat session** is scoped to a single user and cannot be accessed by
   another user.
6. A **team member** cannot perform any write operation; such attempts are
   rejected with an explicit denial message.
7. The **weekly report** is generated once per week and does not repeat on
   failure — a failed delivery is logged but does not block the schedule.
8. Each project has at most one **personal stage set** that is shared across
   the ecosystem.

---

## 6. Non-Functional Aspects

- **Usability:** The chat interface responds in natural language and must be
  usable by non-technical users.
- **Performance:** The system should return a chat response within fifteen
  seconds for ninety percent of requests.
- **Reliability:** The system must handle AI provider rate limits gracefully
  by retrying failed requests.
- **Security:** All write operations are protected by role-based access
  control and executed under an authenticated Odoo user.
- **Extensibility:** The system must allow adding new AI providers, new
  specialized agents, and new tools without modifying the existing codebase.
- **Internationalization:** All user-facing strings, agent instructions, and
  documentation must be written in English.
- **Attribution:** Every page of the ecosystem must display the author and
  institutional copyright.

---

## 7. Out of Scope

The following aspects are explicitly out of scope for version 1.0 of the
case study definition:

- Real-time collaboration features (simultaneous editing of the same task).
- Advanced access-control beyond the two roles (Project Manager, Team Member).
- Integration with external issue trackers (Jira, GitHub Issues, etc.).
- Authentication through identity providers (SSO, OAuth).
- Mobile applications.
- Fine-grained audit logs per field.

---

*End of case study definition.*
