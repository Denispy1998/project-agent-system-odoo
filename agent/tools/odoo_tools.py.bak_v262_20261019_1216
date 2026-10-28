# -*- coding: utf-8 -*-
"""Odoo XML-RPC Tools for CrewAI agents.
All write tools are IDEMPOTENT with UNIFIED responses: the same message is
returned whether the object was just created or already existed.
"""
import xmlrpc.client
import os
from dotenv import load_dotenv
from crewai.tools import tool

load_dotenv('/home/denispy/project-agent-system/.env')

ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "odoo")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

_connection = None


def _get_connection():
    global _connection
    if _connection is not None:
        return _connection
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    if not uid:
        raise ConnectionError("Odoo authentication failed")
    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
    _connection = (common, uid, models)
    return _connection


def _call(model: str, method: str, args: list, kwargs: dict = None):
    _, uid, models = _get_connection()
    return models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, model, method, args, kwargs or {})


def _clean(name: str) -> str:
    if not name:
        return ""
    return name.strip().strip('"').strip("'").strip()


def _find_project(name: str):
    name = _clean(name)
    if not name:
        return None
    ids = _call('project.project', 'search',
                [[('name', '=', name)]], {'order': 'id asc', 'limit': 1})
    if ids:
        return ids[0]
    ids = _call('project.project', 'search',
                [[('name', 'ilike', name)]], {'order': 'id asc', 'limit': 1})
    return ids[0] if ids else None


def _find_task(project_id: int, task_name: str):
    task_name = _clean(task_name)
    if not task_name:
        return None
    ids = _call('project.task', 'search',
                [[('project_id', '=', project_id), ('name', '=', task_name)]],
                {'limit': 1})
    if ids:
        return ids[0]
    ids = _call('project.task', 'search',
                [[('project_id', '=', project_id), ('name', 'ilike', task_name)]],
                {'limit': 1})
    return ids[0] if ids else None


def _find_stage(project_id: int, stage_name: str):
    stage_name = _clean(stage_name)
    if not stage_name:
        return None
    ids = _call('project.task.type', 'search',
                [[('name', '=', stage_name), ('project_ids', 'in', [project_id])]])
    if ids:
        return ids[0]
    ids = _call('project.task.type', 'search',
                [[('name', 'ilike', stage_name), ('project_ids', 'in', [project_id])]])
    return ids[0] if ids else None


# =============================================================================
# READ TOOLS
# =============================================================================
@tool("list_projects")
def list_projects() -> str:
    """List all projects with task counts."""
    ids = _call('project.project', 'search', [[]])
    if not ids:
        return "INFO: No projects found."
    projects = _call('project.project', 'read', [ids], {'fields': ['name', 'task_ids']})
    lines = ["Existing projects:"]
    for p in projects:
        lines.append(f"  • {p['name']} (ID: {p['id']}) – {len(p['task_ids'])} tasks")
    return "\n".join(lines)


@tool("list_tasks")
def list_tasks(project_name: str = "") -> str:
    """List tasks of a project, or all tasks if project_name is empty."""
    # No project → list ALL tasks
    if not project_name or not project_name.strip():
        task_ids = _call('project.task', 'search', [[]])
        if not task_ids:
            return "INFO: No tasks found."
        tasks = _call('project.task', 'read', [task_ids],
                      {'fields': ['name', 'stage_id', 'project_id']})
        lines = [f"All tasks ({len(tasks)} total):"]
        for t in tasks[:50]:
            stage = "No Stage" if not t['stage_id'] else t['stage_id'][1]
            proj = "No Project" if not t.get('project_id') else t['project_id'][1]
            lines.append(f"  • {t['name']} (Project: {proj} | Stage: {stage})")
        if len(tasks) > 50:
            lines.append(f"  ... and {len(tasks) - 50} more")
        return "\n".join(lines)

    # Specific project
    proj_id = _find_project(project_name)
    if not proj_id:
        return f"ERROR: Project '{project_name}' not found."
    task_ids = _call('project.task', 'search', [[('project_id', '=', proj_id)]])
    if not task_ids:
        return f"INFO: Project '{project_name}' has no tasks."
    tasks = _call('project.task', 'read', [task_ids],
                  {'fields': ['name', 'stage_id', 'task_status']})
    lines = [f"Tasks of '{project_name}':"]
    for t in tasks:
        stage = "No Stage" if not t['stage_id'] else t['stage_id'][1]
        status = t.get('task_status') or 'in_backlog'
        lines.append(f"  • {t['name']} (Stage: {stage} | Status: {status})")
    return "\n".join(lines)


@tool("list_stages")
def list_stages(project_name: str) -> str:
    """List all stages of a project."""
    proj_id = _find_project(project_name)
    if not proj_id:
        return f"ERROR: Project '{project_name}' not found."
    stage_ids = _call('project.task.type', 'search', [[('project_ids', 'in', [proj_id])]])
    if not stage_ids:
        return f"INFO: Project '{project_name}' has no stages."
    stages = _call('project.task.type', 'read', [stage_ids], {'fields': ['name', 'sequence']})
    stages.sort(key=lambda s: s.get('sequence', 0))
    lines = [f"Stages of '{project_name}':"]
    for s in stages:
        lines.append(f"  • {s['name']} (ID: {s['id']}, sequence: {s.get('sequence', 0)})")
    return "\n".join(lines)


@tool("analyze_risks")
def analyze_risks(project_name: str) -> str:
    """Analyze risk based on tasks without stage."""
    proj_id = _find_project(project_name)
    if not proj_id:
        return f"ERROR: Project '{project_name}' not found."
    task_ids = _call('project.task', 'search', [[('project_id', '=', proj_id)]])
    if not task_ids:
        return f"INFO: Project '{project_name}' has no tasks."
    tasks = _call('project.task', 'read', [task_ids], {'fields': ['name', 'stage_id']})
    total = len(tasks)
    no_stage = sum(1 for t in tasks if not t['stage_id'])
    risk = (no_stage / total * 100) if total else 0
    return (
        f"Risk analysis for '{project_name}':\n"
        f"  • Total tasks: {total}\n"
        f"  • Tasks without stage: {no_stage}\n"
        f"  • Estimated delay probability: {risk:.1f}%\n"
        f"  • Recommendation: "
        + ("Prioritize stage definition." if risk > 70
           else "Consider assigning stages." if risk > 40
           else "Project is well organized.")
    )


@tool("prioritize_tasks")
def prioritize_tasks(project_name: str) -> str:
    """Prioritize tasks (no-stage first)."""
    proj_id = _find_project(project_name)
    if not proj_id:
        return f"ERROR: Project '{project_name}' not found."
    task_ids = _call('project.task', 'search', [[('project_id', '=', proj_id)]])
    if not task_ids:
        return f"INFO: Project '{project_name}' has no tasks."
    tasks = _call('project.task', 'read', [task_ids], {'fields': ['name', 'stage_id']})
    sorted_tasks = sorted(tasks, key=lambda t: (0 if not t['stage_id'] else 1, t['name']))
    lines = [f"Tasks of '{project_name}' by priority:"]
    for i, t in enumerate(sorted_tasks, 1):
        stage = "No Stage" if not t['stage_id'] else t['stage_id'][1]
        lines.append(f"  {i}. {t['name']} (Stage: {stage})")
    return "\n".join(lines)


@tool("project_summary")
def project_summary(project_name: str) -> str:
    """Full summary of a project: tasks, stages, risks, progress."""
    proj_id = _find_project(project_name)
    if not proj_id:
        return f"ERROR: Project '{project_name}' not found."
    tasks = _call('project.task', 'search', [[('project_id', '=', proj_id)]])
    task_data = _call('project.task', 'read', [tasks], {'fields': ['name', 'stage_id']}) if tasks else []
    stage_ids = _call('project.task.type', 'search', [[('project_ids', 'in', [proj_id])]])
    stage_data = _call('project.task.type', 'read', [stage_ids], {'fields': ['name']}) if stage_ids else []
    total = len(task_data)
    no_stage = sum(1 for t in task_data if not t['stage_id'])
    stage_counts = {}
    for t in task_data:
        stage_name = t['stage_id'][1] if t['stage_id'] else "No Stage"
        stage_counts[stage_name] = stage_counts.get(stage_name, 0) + 1
    risk = (no_stage / total * 100) if total else 0
    risk_label = "HIGH" if risk > 70 else "MEDIUM" if risk > 40 else "LOW"
    lines = [
        f"Project Summary: {project_name}",
        "=" * 50,
        f"Total tasks: {total}",
        f"Total stages: {len(stage_data)}",
        f"Tasks without stage: {no_stage}",
        f"Risk level: {risk_label} ({risk:.1f}%)",
        "",
        "Tasks by stage:",
    ]
    for sname, count in sorted(stage_counts.items()):
        lines.append(f"  • {sname}: {count} task(s)")
    return "\n".join(lines)


# =============================================================================
# WRITE TOOLS (unified idempotent responses)
# =============================================================================
@tool("create_project")
def create_project(name: str, tasks: str = "") -> str:
    """Create a project with optional tasks. Idempotent with unified response."""
    name = _clean(name)
    if not name:
        return "ERROR: Project name cannot be empty."
    proj_id = _find_project(name)
    if not proj_id:
        proj_id = _call('project.project', 'create', [{'name': name}])
        task_list = [_clean(t) for t in tasks.split(',') if _clean(t)]
        for tname in task_list:
            if not _find_task(proj_id, tname):
                try:
                    _call('project.task', 'create', [{
                        'name': tname, 'project_id': proj_id, 'stage_id': False,
                    }])
                except Exception:
                    pass
    return (f"Project '{name}' (ID {proj_id}) is ready. "
            f"Action complete. Do NOT retry.")


@tool("add_task")
def add_task(project_name: str, task_name: str) -> str:
    """Add a task to a project. Idempotent with unified response."""
    task_name = _clean(task_name)
    if not task_name:
        return "ERROR: Task name cannot be empty."
    proj_id = _find_project(project_name)
    if not proj_id:
        return f"ERROR: Project '{project_name}' not found."
    task_id = _find_task(proj_id, task_name)
    if not task_id:
        try:
            task_id = _call('project.task', 'create', [{
                'name': task_name, 'project_id': proj_id, 'stage_id': False,
            }])
        except Exception as e:
            return f"ERROR: Failed to create task '{task_name}': {e}"
        if not task_id:
            return f"ERROR: Task '{task_name}' could not be created (create returned no id)."
        # verify it persisted
        verified = _call('project.task', 'search_count',
                         [[('id', '=', task_id), ('project_id', '=', proj_id)]])
        if not verified:
            return (f"ERROR: Task '{task_name}' was created but not linked "
                    f"to project '{project_name}'.")
    return (f"Task '{task_name}' is ready in project '{project_name}' "
            f"(ID {task_id}). Action complete. Do NOT retry.")


@tool("create_stage")
def create_stage(project_name: str, stage_name: str, sequence: int = 10) -> str:
    """Create a stage in a project. Idempotent with unified response."""
    stage_name = _clean(stage_name)
    if not stage_name:
        return "ERROR: Stage name cannot be empty."
    proj_id = _find_project(project_name)
    if not proj_id:
        return f"ERROR: Project '{project_name}' not found."
    stage_id = _find_stage(proj_id, stage_name)
    if not stage_id:
        stage_id = _call('project.task.type', 'create', [{
            'name': stage_name, 'sequence': sequence, 'project_ids': [(4, proj_id)],
        }])
    else:
        # Ensure it's linked to this project
        linked = _call('project.task.type', 'search',
                       [[('id', '=', stage_id), ('project_ids', 'in', [proj_id])]])
        if not linked:
            _call('project.task.type', 'write',
                  [[stage_id], {'project_ids': [(4, proj_id)]}])
    return (f"Stage '{stage_name}' is ready in project '{project_name}' "
            f"(ID {stage_id}). Action complete. Do NOT retry.")


@tool("move_single_task")
def move_single_task(project_name: str, task_name: str, target_stage_name: str) -> str:
    """Move ONE task to a different stage."""
    proj_id = _find_project(project_name)
    if not proj_id:
        return f"ERROR: Project '{project_name}' not found."
    task_id = _find_task(proj_id, task_name)
    if not task_id:
        return f"ERROR: Task '{task_name}' not found in project '{project_name}'."
    stage_id = _find_stage(proj_id, target_stage_name)
    if not stage_id:
        return (f"ERROR: Stage '{target_stage_name}' not found in project "
                f"'{project_name}'. Create it first with create_stage.")
    _call('project.task', 'write', [[task_id], {'stage_id': stage_id}])
    return (f"Task '{task_name}' is now in stage '{target_stage_name}'. "
            f"Action complete. Do NOT retry.")


@tool("move_tasks")
def move_tasks(project_name: str, task_names_csv: str, target_stage_name: str) -> str:
    """Move MULTIPLE tasks to a target stage."""
    proj_id = _find_project(project_name)
    if not proj_id:
        return f"ERROR: Project '{project_name}' not found."
    stage_id = _find_stage(proj_id, target_stage_name)
    if not stage_id:
        return f"ERROR: Stage '{target_stage_name}' not found in project '{project_name}'."
    names = [_clean(n) for n in task_names_csv.split(',') if _clean(n)]
    moved, missing = [], []
    for name in names:
        tid = _find_task(proj_id, name)
        if tid:
            _call('project.task', 'write', [[tid], {'stage_id': stage_id}])
            moved.append(name)
        else:
            missing.append(name)
    msg = (f"{len(moved)} task(s) are now in stage '{target_stage_name}': "
           f"{', '.join(moved)}. Action complete. Do NOT retry.")
    if missing:
        msg += f"\n  Not found: {', '.join(missing)}"
    return msg


@tool("delete_task")
def delete_task(project_name: str, task_name: str) -> str:
    """Delete ALL tasks with the given name in the project."""
    task_name = _clean(task_name)
    if not task_name:
        return "ERROR: Task name cannot be empty."
    proj_id = _find_project(project_name)
    if not proj_id:
        return f"ERROR: Project '{project_name}' not found."
    ids = _call('project.task', 'search',
                [[('project_id', '=', proj_id), ('name', '=', task_name)]])
    if not ids:
        ids = _call('project.task', 'search',
                    [[('project_id', '=', proj_id), ('name', 'ilike', task_name)]])
    if ids:
        _call('project.task', 'unlink', [ids])
    return (f"Task '{task_name}' is no longer present in project "
            f"'{project_name}'. Action complete. Do NOT retry.")


@tool("delete_stage")
def delete_stage(project_name: str, stage_name: str) -> str:
    """Delete a stage. Only works if it has no tasks."""
    proj_id = _find_project(project_name)
    if not proj_id:
        return f"ERROR: Project '{project_name}' not found."
    stage_id = _find_stage(proj_id, stage_name)
    if not stage_id:
        return (f"Stage '{stage_name}' is no longer present in project "
                f"'{project_name}'. Action complete. Do NOT retry.")
    # Count tasks of THIS project using the stage
    in_use = _call('project.task', 'search_count',
                   [[('stage_id', '=', stage_id), ('project_id', '=', proj_id)]])
    if in_use:
        return (f"ERROR: Cannot delete stage '{stage_name}' — it has {in_use} "
                f"task(s) assigned in this project. Move or delete them first.")

    # Remove the stage from THIS project only (M2M unlink, not record delete)
    _call('project.task.type', 'write', [[stage_id], {'project_ids': [(3, proj_id)]}])

    # If the stage is no longer linked to ANY project AND has no tasks,
    # it can be safely deleted
    linked = _call('project.task.type', 'read', [[stage_id], ['project_ids']])
    remaining = linked[0].get('project_ids', []) if linked else []
    if not remaining:
        any_task = _call('project.task', 'search_count', [[('stage_id', '=', stage_id)]])
        if not any_task:
            try:
                _call('project.task.type', 'unlink', [[stage_id]])
            except Exception:
                pass  # Already unlinked from all projects, keep as orphan

    return (f"Stage '{stage_name}' is no longer present in project "
            f"'{project_name}'. Action complete. Do NOT retry.")


@tool("delete_project")
def delete_project(project_name: str) -> str:
    """Delete a project AND all its tasks."""
    proj_id = _find_project(project_name)
    if not proj_id:
        return (f"Project '{project_name}' is no longer present in the system. "
                f"Action complete. Do NOT retry.")
    task_ids = _call('project.task', 'search', [[('project_id', '=', proj_id)]])
    if task_ids:
        _call('project.task', 'unlink', [task_ids])
    _call('project.project', 'unlink', [[proj_id]])
    return (f"Project '{project_name}' is no longer present in the system. "
            f"Action complete. Do NOT retry.")



@tool("move_all_tasks")
def move_all_tasks(project_name: str, target_stage_name: str) -> str:
    """Move ALL tasks of a project to a target stage."""
    proj_id = _find_project(project_name)
    if not proj_id:
        return f"ERROR: Project '{project_name}' not found."
    stage_id = _find_stage(proj_id, target_stage_name)
    if not stage_id:
        return f"ERROR: Stage '{target_stage_name}' not found in project '{project_name}'."
    task_ids = _call('project.task', 'search', [[('project_id', '=', proj_id)]])
    if not task_ids:
        return f"No tasks in project '{project_name}'. Action complete. Do NOT retry."
    _call('project.task', 'write', [task_ids, {'stage_id': stage_id}])
    return (f"{len(task_ids)} task(s) moved to stage '{target_stage_name}' "
            f"in project '{project_name}'. Action complete. Do NOT retry.")


# =============================================================================
# STATUS TOOLS
# =============================================================================

# Natural-language synonyms → canonical task_status values
_STATUS_SYNONYMS = {
    # in_backlog
    "in_backlog": "in_backlog",
    "inbacklog":  "in_backlog",
    "backlog":    "in_backlog",
    "todo":       "in_backlog",
    "to_do":      "in_backlog",
    "not_started": "in_backlog",
    # in_progress
    "in_progress": "in_progress",
    "inprogress":  "in_progress",
    "in-progress": "in_progress",
    "progress":    "in_progress",
    "doing":       "in_progress",
    "wip":         "in_progress",
    "working":     "in_progress",
    # concluded
    "concluded":  "concluded",
    "done":       "concluded",
    "complete":   "concluded",
    "completed":  "concluded",
    "finished":   "concluded",
    "closed":     "concluded",
}


def _normalize_status(raw: str):
    """Map a natural-language status string to a canonical task_status value."""
    if not raw:
        return None
    s = _clean(raw).lower().strip().replace(" ", "_")
    return _STATUS_SYNONYMS.get(s)


@tool("set_task_status")
def set_task_status(project_name: str, task_name: str, new_status: str) -> str:
    """Change the lifecycle status of a task: in_backlog, in_progress, or concluded.

    Accepts synonyms: 'done'/'completed'/'finished' → concluded;
    'doing'/'working'/'wip' → in_progress; 'todo'/'backlog' → in_backlog.

    The Odoo model auto-fills date_end when the status becomes concluded
    and clears it when it moves back to in_backlog or in_progress.
    """
    normalized = _normalize_status(new_status)
    if not normalized:
        return (f"ERROR: Invalid status '{new_status}'. "
                f"Use one of: in_backlog, in_progress, concluded.")

    proj_id = _find_project(project_name)
    if not proj_id:
        return f"ERROR: Project '{project_name}' not found."

    task_id = _find_task(proj_id, task_name)
    if not task_id:
        return f"ERROR: Task '{task_name}' not found in project '{project_name}'."

    _call('project.task', 'write', [[task_id], {'task_status': normalized}])
    return (f"Task '{task_name}' status is now '{normalized}'. "
            f"Action complete. Do NOT retry.")



# =============================================================================
# SERVER-SIDE PERMISSION CHECK (v2.5)
# =============================================================================
# The FastAPI layer used to trust the is_manager flag sent by the client.
# A direct POST to :8001 with is_manager=true would execute writes even
# for a Team Member. These helpers verify the user role in Odoo via
# XML-RPC before the orchestrator ever sees the request.

_MANAGER_CACHE = {}
_MANAGER_CACHE_TTL = 60


def _user_is_manager_via_xmlrpc(user_id):
    """Query Odoo for the actual group membership of user_id."""
    if not user_id:
        return False
    try:
        rows = _call("res.users", "read",
                     [[user_id]],
                     {"fields": ["login", "group_ids"]})
        if not rows:
            return False
        user = rows[0]
        # Fast-path: admin by login
        if user.get("login") == "admin":
            return True
        # Real check 1: Gestor de Projeto group by name
        grp_ids = _call("res.groups", "search",
                        [[["name", "=", "Gestor de Projeto"]]],
                        {"limit": 1})
        if grp_ids and grp_ids[0] in (user.get("group_ids") or []):
            return True
        # Real check 2: built-in system group (superuser / admin equivalent)
        sys_ids = _call("ir.model.data", "search_read",
                        [[["module", "=", "base"],
                          ["name", "=", "group_system"]]],
                        {"fields": ["res_id"], "limit": 1})
        if sys_ids and sys_ids[0].get("res_id") in (user.get("group_ids") or []):
            return True
        return False
    except Exception as e:
        print(f"[verify_manager] XML-RPC error for user_id={user_id}: {e}")
        return False


def verify_user_is_manager(user_id):
    """Public, cached version. Falls back to False on any error."""
    import time
    now = time.time()
    cached = _MANAGER_CACHE.get(user_id)
    if cached and cached[0] > now:
        return cached[1]
    result = _user_is_manager_via_xmlrpc(user_id)
    _MANAGER_CACHE[user_id] = (now + _MANAGER_CACHE_TTL, result)
    return result
