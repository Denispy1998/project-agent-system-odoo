#!/usr/bin/env python3
# Smoke test for the AI Project Management Ecosystem (v2.5.0)
#
# Runs ~20 checks against the live system and prints PASS/FAIL per test.
# Exit 0 if all PASS (SKIP allowed), 1 otherwise.
#
# Usage:
#     cd ~/project-agent-system
#     source venv_agents/bin/activate
#     python3 tests/smoke_test.py

import sys
import time
from datetime import datetime

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. pip install requests")
    sys.exit(2)

# --- Config ---
FASTAPI = "http://127.0.0.1:8001"
ODOO = "http://127.0.0.1:8069"
TIMEOUT = 120  # seconds per request (LLM fallback can be slow)

ADMIN_ID = 2  # actual admin id in Odoo (id=1 is OdooBot / __system__)
JOAO_ID = 5
JOSE_ID = 6

results = []  # list of (name, status, detail)


def call_agent(message, user_id=2, is_manager=True, model_name="groq"):
    """Returns the response string, or an ERROR:... string on failure.
    Never raises — the smoke test must report failures, not crash."""
    try:
        r = requests.post(
            FASTAPI + "/agent/run",
            json={"message": message, "user_id": user_id,
                  "is_manager": is_manager, "model_name": model_name},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json().get("response", "")
    except requests.exceptions.ConnectionError:
        return "ERROR: FastAPI unreachable"
    except requests.exceptions.Timeout:
        return "ERROR: request timeout"
    except Exception as e:
        return "ERROR: " + type(e).__name__ + ": " + str(e)[:80]


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    marker = "[PASS]" if condition else "[FAIL]"
    print("  " + marker + " " + name + ("  -- " + detail if detail else ""))


def skip(name, reason):
    results.append((name, "SKIP", reason))
    print("  [SKIP] " + name + "  -- " + reason)


def section(title):
    print()
    print("=== " + title + " ===")


# ----------------------------------------------------------------
# 1. SERVICE HEALTH
# ----------------------------------------------------------------
def test_services():
    section("1. Services")
    try:
        r = requests.get(FASTAPI + "/health", timeout=5)
        check("FastAPI /health",
              r.status_code == 200 and r.json().get("status") == "ok")
    except Exception as e:
        check("FastAPI /health", False, str(e))

    try:
        r = requests.get(ODOO + "/web/login", timeout=5)
        check("Odoo /web/login reachable", r.status_code == 200)
    except Exception as e:
        check("Odoo /web/login reachable", False, str(e))


# ----------------------------------------------------------------
# 2. ROUTER LOCAL (no LLM, fast)
# ----------------------------------------------------------------
def test_router_local():
    section("2. Router local (no LLM)")

    t0 = time.time()
    r = call_agent("list all projects")
    check("list all projects",
          "Demonstracao" in r or "Existing projects" in r,
          "{:.2f}s".format(time.time() - t0))

    t0 = time.time()
    r = call_agent("list all tasks")
    check("list all tasks",
          "All tasks" in r or "Tasks of" in r,
          "{:.2f}s".format(time.time() - t0))

    r = call_agent("list stages in Sistema Empresarial")
    check("list stages in project", "Stages of" in r or "TO_MAKE" in r)

    r = call_agent("analyze risks of Sistema Empresarial")
    check("analyze risks", "Risk" in r or "risk" in r)

    r = call_agent("summary of Sistema Empresarial")
    check("project summary", "Summary" in r or "Total" in r)


# ----------------------------------------------------------------
# 3. DIAGRAM GENERATION (LLM shortcut)
# ----------------------------------------------------------------
def test_diagrams():
    section("3. Diagrams (LLM shortcut)")

    cases = [
        ("state diagram for task lifecycle", "stateDiagram"),
        ("er diagram for user project task", "erDiagram"),
        ("sequence diagram of login flow", "sequenceDiagram"),
    ]
    for msg, expected in cases:
        try:
            t0 = time.time()
            r = call_agent(msg)
            if not (expected in r) and "Rate limit" in r:
                skip(msg, "rate-limited")
                continue
            check(msg, expected in r, "{:.2f}s".format(time.time() - t0))
        except Exception as e:
            check(msg, False, str(e))


# ----------------------------------------------------------------
# 4. TASK STATUS TOOL
# ----------------------------------------------------------------
def test_task_status():
    section("4. Task status tool")

    r = call_agent("set task Task-1 in Sistema Hospitalar to in_progress", user_id=ADMIN_ID)
    check("set task to in_progress",
          "in_progress" in r or "Action complete" in r)

    r = call_agent("list all tasks")
    check("verify status via list",
          "Task-1" in r and ("in_progress" in r.lower() or "in progress" in r.lower()))


# ----------------------------------------------------------------
# 5. RBAC + SERVER-SIDE VERIFICATION (v2.5)
# ----------------------------------------------------------------
def test_rbac():
    section("5. RBAC + server-side verification (v2.5)")

    r = call_agent("list all projects", user_id=JOSE_ID, is_manager=False)
    check("jose reads (is_manager=false)",
          "Existing projects" in r or "Demonstracao" in r)

    r = call_agent("create project SmokeTest_A", user_id=JOSE_ID, is_manager=False)
    check("jose write (is_manager=false) DENIED", r.startswith("DENIED"))

    r = call_agent("create project SmokeTest_B", user_id=JOSE_ID, is_manager=True)
    ok = r.startswith("DENIED")
    check("jose write (LYING is_manager=true) DENIED", ok,
          "server-side downgrade OK" if ok else "v2.5 FAILED")

    r = call_agent("set task Task-1 in Sistema Hospitalar to in_backlog",
                   user_id=JOAO_ID, is_manager=True)
    check("joao real manager can write",
          "Action complete" in r or "in_backlog" in r)


# ----------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------
def main():
    print("==========================================================")
    print("  SMOKE TEST -- AI Project Management Ecosystem (v2.5.0)")
    print("==========================================================")
    print("Started at " + datetime.now().isoformat(timespec="seconds"))

    test_services()
    test_router_local()
    test_diagrams()
    test_task_status()
    test_rbac()

    print()
    print("==========================================================")
    print("                      RESULTS")
    print("==========================================================")
    passed = sum(1 for _, s, _ in results if s == "PASS")
    skipped = sum(1 for _, s, _ in results if s == "SKIP")
    failed = sum(1 for _, s, _ in results if s == "FAIL")
    total = len(results)
    print("  Total:  " + str(total))
    print("  PASS:   " + str(passed))
    print("  SKIP:   " + str(skipped))
    print("  FAIL:   " + str(failed))

    if failed:
        print()
        print("  Failures:")
        for n, s, d in results:
            if s == "FAIL":
                print("    - " + n + "  " + d)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
