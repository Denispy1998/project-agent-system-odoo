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
