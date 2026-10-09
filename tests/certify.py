#!/usr/bin/env python3
"""Certification script for the AI Project Management Ecosystem.

Runs a comprehensive audit against the live system and prints a
final PASS/FAIL certificate. Designed for the PIC2 evidence trail.

Usage:
    cd ~/project-agent-system
    source venv_agents/bin/activate
    python3 tests/certify.py
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests

FASTAPI = "http://127.0.0.1:8001"
ODOO = "http://127.0.0.1:8069"
ROOT = Path(__file__).resolve().parents[1]

results = []


def section(title):
    print()
    print("=" * 62)
    print("  " + title)
    print("=" * 62)


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    marker = "[OK]  " if ok else "[FAIL]"
    print("  " + marker + " " + name + ("  (" + detail + ")" if detail else ""))


# ─────────────────────────────────────────────────────────────
# 1. Services
# ─────────────────────────────────────────────────────────────
section("1. SERVICES")

try:
    r = requests.get(FASTAPI + "/health", timeout=10)
    h = r.json()
    check("FastAPI /health reachable", r.status_code == 200)
    check("FastAPI /health status=ok", h.get("status") == "ok",
          "version=" + str(h.get("version")))
    comps = h.get("components", {})
    check("  odoo component ok",
          comps.get("odoo", {}).get("status") == "ok",
          "latency=" + str(comps.get("odoo", {}).get("latency_ms")) + "ms")
    check("  groq_key component ok",
          comps.get("groq_key", {}).get("status") == "ok")
except Exception as e:
    check("FastAPI /health reachable", False, str(e)[:80])

try:
    r = requests.get(ODOO + "/web/login", timeout=10)
    check("Odoo /web/login reachable", r.status_code == 200)
except Exception as e:
    check("Odoo /web/login reachable", False, str(e)[:80])


# ─────────────────────────────────────────────────────────────
# 2. Router local — all main intents (~0.2s each)
# ─────────────────────────────────────────────────────────────
section("2. ROUTER LOCAL")

def call(msg, uid=2, mgr=True):
    try:
        r = requests.post(
            FASTAPI + "/agent/run",
            json={"message": msg, "user_id": uid,
                  "is_manager": mgr, "model_name": "groq"},
            timeout=120,
        )
        return r.json().get("response", "")
    except Exception as e:
        return "ERR: " + str(e)[:60]

router_tests = [
    ("list all projects",     ["Existing projects", "Demonstra"]),
    ("list all tasks",        ["All tasks", "Tasks of"]),
    ("list tasks in Sistema Hospitalar", ["Tasks of", "Sistema Hospitalar"]),
    ("list stages in Sistema Empresarial", ["Stages of", "TO_MAKE", "DESIGN"]),
    ("analyze risks of Sistema Empresarial", ["Risk", "risk"]),
    ("summary of Sistema Empresarial", ["Summary", "Total"]),
]
for msg, keywords in router_tests:
    r = call(msg)
    ok = any(k in r for k in keywords)
    check("  " + msg[:45], ok, ("routed" if ok else r[:50]))


# ─────────────────────────────────────────────────────────────
# 3. Diagram shortcut (7 kinds)
# ─────────────────────────────────────────────────────────────
section("3. DIAGRAMS (all 7 kinds)")

diagrams = [
    ("flowchart",  "flowchart of a deployment process"),
    ("sequence",   "sequence diagram of the login flow"),
    ("er",         "er diagram for user project task"),
    ("class",      "class diagram for project management"),
    ("state",      "state diagram for task lifecycle"),
    ("gantt",      "gantt chart for the roadmap"),
    ("pie",        "pie chart of task distribution"),
]
expected = {
    "flowchart": "flowchart", "sequence": "sequenceDiagram",
    "er": "erDiagram", "class": "classDiagram",
    "state": "stateDiagram", "gantt": "gantt", "pie": "pie",
}
for kind, msg in diagrams:
    r = call(msg)
    if "Rate limit" in r:
        check("  diagram " + kind, False, "rate limited")
    else:
        check("  diagram " + kind, expected[kind] in r)


# ─────────────────────────────────────────────────────────────
# 4. Task lifecycle via chat
# ─────────────────────────────────────────────────────────────
section("4. TASK LIFECYCLE VIA CHAT")

r = call("set task Task-1 in Sistema Hospitalar to in_progress")
check("  set to in_progress", "Action complete" in r or "in_progress" in r)

r = call("list tasks in Sistema Hospitalar")
check("  verify status via list",
      "Task-1" in r and ("in_progress" in r.lower() or "in progress" in r.lower()))

r = call("set task Task-1 in Sistema Hospitalar to in_backlog")
check("  reset to in_backlog", "Action complete" in r or "in_backlog" in r)


# ─────────────────────────────────────────────────────────────
# 5. RBAC + server-side verification
# ─────────────────────────────────────────────────────────────
section("5. RBAC + SERVER-SIDE VERIFICATION")

r = call("list all projects", uid=6, mgr=False)
check("  jose reads (member)", "Existing projects" in r or "Demonstra" in r)

r = call("create project CERT_ShouldFail", uid=6, mgr=False)
check("  jose write (member) DENIED", r.startswith("DENIED"))

r = call("create project CERT_ShouldFail2", uid=6, mgr=True)
check("  jose write (LYING mgr=true) DENIED", r.startswith("DENIED"),
      "server-side downgrade")

r = call("set task Task-1 in Sistema Hospitalar to concluded", uid=5, mgr=True)
check("  joao real Manager can write", "Action complete" in r)

r = call("set task Task-1 in Sistema Hospitalar to in_backlog", uid=5, mgr=True)
check("  joao resets Task-1", "Action complete" in r)


# ─────────────────────────────────────────────────────────────
# 6. Pytest unit suite
# ─────────────────────────────────────────────────────────────
section("6. PYTEST UNIT SUITE (44 tests)")

pytest_proc = subprocess.run(
    [sys.executable, "-m", "pytest", str(ROOT / "tests" / "unit"), "-q"],
    capture_output=True, text=True, cwd=str(ROOT),
)
last_line = pytest_proc.stdout.strip().splitlines()[-1] if pytest_proc.stdout else ""
check("  pytest tests/unit/", pytest_proc.returncode == 0, last_line[:70])


# ─────────────────────────────────────────────────────────────
# 7. Log audit — last 200 lines
# ─────────────────────────────────────────────────────────────
section("7. LOG AUDIT")

def log_errors(path, n=200):
    if not os.path.exists(path):
        return "no file"
    try:
        with open(path, errors="replace") as f:
            tail = f.readlines()[-n:]
        return sum(1 for l in tail
                   if "Traceback" in l or " CRITICAL " in l)
    except Exception as e:
        return str(e)

fastapi_err = log_errors("/tmp/agents_api.log")
odoo_err = log_errors(os.path.expanduser("~/odoo.log"))
check("  FastAPI log  (last 200 lines, 0 expected)", fastapi_err == 0,
      str(fastapi_err))
check("  Odoo log     (last 200 lines, 0 expected)", odoo_err == 0,
      str(odoo_err))


# ─────────────────────────────────────────────────────────────
# 8. Version consistency
# ─────────────────────────────────────────────────────────────
section("8. VERSION CONSISTENCY")

def read_api_version():
    candidates = [
        ROOT / "agents_api" / "main.py",
        ROOT / "agent" / "agents_api" / "main.py",
    ]
    for p in candidates:
        if p.exists():
            for line in p.read_text().splitlines():
                if "API_VERSION" in line and "=" in line:
                    return line.split("=", 1)[1].strip().strip("'\"")
    return "?"

api_ver = read_api_version()
check("  FastAPI API_VERSION", api_ver.startswith("2.5"), api_ver)


# ─────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────
section("CERTIFICATION SUMMARY")

total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
failed = total - passed

print()
print("  Total  : " + str(total))
print("  Passed : " + str(passed))
print("  Failed : " + str(failed))
print()
print("  Timestamp: " + datetime.now().isoformat(timespec="seconds"))
print()

if failed:
    print("  FAILURES:")
    for n, ok, d in results:
        if not ok:
            print("    - " + n + "  " + d)
    print()
    print("  >>> ECOSYSTEM: NOT CERTIFIED <<<")
    sys.exit(1)
else:
    print("  >>> ECOSYSTEM: CERTIFIED OK <<<")
    sys.exit(0)
