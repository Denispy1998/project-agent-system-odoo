# -*- coding: utf-8 -*-
"""Jira XML-REST API Tools for CrewAI agents."""
import os
import requests
import base64
from dotenv import load_dotenv
from crewai.tools import tool

load_dotenv('/home/denispy/project-agent-system/.env', override=True)

JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

def _get_headers():
    if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
        raise ValueError("Jira credentials missing in .env")
    auth_str = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    return {
        "Authorization": f"Basic {b64_auth}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

@tool("list_jira_projects")
def list_jira_projects() -> str:
    """List all projects available in the connected Jira workspace."""
    try:
        headers = _get_headers()
        response = requests.get(f"{JIRA_URL}/rest/api/3/project", headers=headers, timeout=10)
        response.raise_for_status()
        projects = response.json()

        if not projects:
            return "INFO: No projects found in Jira."

        lines = ["Jira Projects:"]
        for p in projects:
            lines.append(f"  • {p['key']}: {p['name']} (ID: {p['id']})")
        return "\n".join(lines)
    except Exception as e:
        return f"ERROR: Failed to list Jira projects: {str(e)}"

@tool("create_jira_issue")
def create_jira_issue(project_key: str, summary: str, description: str = "", issue_type: str = "Task") -> str:
    """Create a new issue in Jira. Requires a project key (e.g., 'KAN'), a summary, and optional description."""
    try:
        headers = _get_headers()
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}]
                        }
                    ]
                },
                "issuetype": {"name": issue_type}
            }
        }
        response = requests.post(f"{JIRA_URL}/rest/api/3/issue", headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        return f"SUCCESS: Jira Issue '{summary}' created (Key: {data['key']}). Action complete."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            return f"ERROR: Invalid data (check project key '{project_key}' and issue type '{issue_type}'). Detail: {e.response.text}"
        return f"ERROR: HTTP {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"ERROR: Failed to create Jira issue: {str(e)}"

@tool("update_jira_issue")
def update_jira_issue(issue_key: str, summary: str = "", description: str = "") -> str:
    """Update an existing Jira issue. Requires the issue key (e.g., 'KAN-4'). You can update the summary and/or description."""
    try:
        headers = _get_headers()
        payload = {"fields": {}}
        
        if summary:
            payload["fields"]["summary"] = summary
            
        if description:
            payload["fields"]["description"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}]
                    }
                ]
            }
            
        if not payload["fields"]:
            return "ERROR: You must provide either a new summary or a new description to update."

        response = requests.put(f"{JIRA_URL}/rest/api/3/issue/{issue_key}", headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return f"SUCCESS: Jira Issue '{issue_key}' updated successfully. Action complete."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return f"ERROR: Issue '{issue_key}' not found in Jira."
        return f"ERROR: HTTP {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"ERROR: Failed to update Jira issue: {str(e)}"

@tool("delete_jira_issue")
def delete_jira_issue(issue_key: str) -> str:
    """Delete an existing Jira issue. Requires the issue key (e.g., 'KAN-4')."""
    try:
        headers = _get_headers()
        response = requests.delete(f"{JIRA_URL}/rest/api/3/issue/{issue_key}", headers=headers, timeout=10)
        response.raise_for_status()
        return f"SUCCESS: Jira Issue '{issue_key}' deleted successfully. Action complete."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return f"ERROR: Issue '{issue_key}' not found in Jira."
        return f"ERROR: HTTP {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"ERROR: Failed to delete Jira issue: {str(e)}"

@tool("move_jira_issue")
def move_jira_issue(issue_key: str, target_status: str) -> str:
    """Move a Jira issue to a new status/column (e.g., 'In Progress', 'Done'). Requires the issue key and the target status name."""
    try:
        headers = _get_headers()
        # 1. Get available transitions for this issue
        res = requests.get(f"{JIRA_URL}/rest/api/3/issue/{issue_key}/transitions", headers=headers, timeout=10)
        res.raise_for_status()
        transitions = res.json().get("transitions", [])

        # 2. Find the transition that leads to the target status
        target_lower = target_status.lower()
        transition_id = None
        for t in transitions:
            if t['name'].lower() == target_lower or t['to']['name'].lower() == target_lower:
                transition_id = t['id']
                break

        if not transition_id:
            available = [f"{t['name']} (-> {t['to']['name']})" for t in transitions]
            return f"ERROR: Transition to '{target_status}' not found. Available transitions: {', '.join(available)}"

        # 3. Execute transition
        payload = {"transition": {"id": transition_id}}
        requests.post(f"{JIRA_URL}/rest/api/3/issue/{issue_key}/transitions", headers=headers, json=payload, timeout=10).raise_for_status()
        return f"SUCCESS: Jira Issue '{issue_key}' moved to '{target_status}'. Action complete."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return f"ERROR: Issue '{issue_key}' not found."
        return f"ERROR: HTTP {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"ERROR: Failed to move Jira issue: {str(e)}"
