"""Unit tests for pure helpers in tools/odoo_tools.py.

XML-RPC calls are NOT exercised. verify_user_is_manager is tested with
a monkeypatched _call to simulate Odoo responses.
"""
import sys

sys.path.insert(0, "/home/denispy/project-agent-system")

import pytest


def test_clean_strips_quotes_and_whitespace():
    from tools.odoo_tools import _clean
    assert _clean('"Hello"') == "Hello"
    assert _clean("'Hello'") == "Hello"
    assert _clean("  Hello  ") == "Hello"
    assert _clean("") == ""


def test_normalize_status_canonical():
    from tools.odoo_tools import _normalize_status
    assert _normalize_status("in_backlog") == "in_backlog"
    assert _normalize_status("in_progress") == "in_progress"
    assert _normalize_status("concluded") == "concluded"


def test_normalize_status_synonyms():
    from tools.odoo_tools import _normalize_status
    # concluded family
    assert _normalize_status("done") == "concluded"
    assert _normalize_status("finished") == "concluded"
    assert _normalize_status("complete") == "concluded"
    assert _normalize_status("completed") == "concluded"
    assert _normalize_status("closed") == "concluded"
    # in_progress family
    assert _normalize_status("doing") == "in_progress"
    assert _normalize_status("wip") == "in_progress"
    assert _normalize_status("working") == "in_progress"
    assert _normalize_status("progress") == "in_progress"
    # in_backlog family
    assert _normalize_status("todo") == "in_backlog"
    assert _normalize_status("backlog") == "in_backlog"


def test_normalize_status_case_insensitive_and_spaces():
    from tools.odoo_tools import _normalize_status
    assert _normalize_status("DONE") == "concluded"
    assert _normalize_status("  In Progress  ") == "in_progress"
    assert _normalize_status("In Progress") == "in_progress"


def test_normalize_status_invalid_returns_none():
    from tools.odoo_tools import _normalize_status
    assert _normalize_status("flying") is None
    assert _normalize_status("") is None
    assert _normalize_status(None) is None


# ----------------------------------------------------------------
# verify_user_is_manager with a mocked _call
# ----------------------------------------------------------------

@pytest.fixture
def odoo_tools(monkeypatch):
    """Import the module and reset its cache + mock _call."""
    from tools import odoo_tools as ot
    ot._MANAGER_CACHE.clear()
    return ot


def _mock_call_factory(rows_users, grp_ids, sys_grp_ids):
    def _mock(model, method, args, kwargs=None):
        if model == "res.users" and method == "read":
            return rows_users
        if model == "res.groups" and method == "search":
            return grp_ids
        if model == "ir.model.data" and method == "search_read":
            return sys_grp_ids
        return []
    return _mock


def test_verify_manager_by_login_admin(odoo_tools, monkeypatch):
    rows = [{"id": 2, "login": "admin", "group_ids": []}]
    monkeypatch.setattr(odoo_tools, "_call",
                        _mock_call_factory(rows, [], []))
    assert odoo_tools.verify_user_is_manager(2) is True


def test_verify_manager_by_gestor_group(odoo_tools, monkeypatch):
    rows = [{"id": 5, "login": "joao", "group_ids": [31, 99]}]
    monkeypatch.setattr(odoo_tools, "_call",
                        _mock_call_factory(rows, [31], []))
    assert odoo_tools.verify_user_is_manager(5) is True


def test_verify_manager_by_system_group(odoo_tools, monkeypatch):
    rows = [{"id": 2, "login": "someuser", "group_ids": [1, 55]}]
    monkeypatch.setattr(odoo_tools, "_call",
                        _mock_call_factory(rows, [], [{"res_id": 1}]))
    assert odoo_tools.verify_user_is_manager(2) is True


def test_verify_manager_returns_false_for_team_member(odoo_tools, monkeypatch):
    rows = [{"id": 6, "login": "jose", "group_ids": [99, 100]}]
    monkeypatch.setattr(odoo_tools, "_call",
                        _mock_call_factory(rows, [31], []))
    assert odoo_tools.verify_user_is_manager(6) is False


def test_verify_manager_empty_user_id(odoo_tools, monkeypatch):
    monkeypatch.setattr(odoo_tools, "_call",
                        _mock_call_factory([], [], []))
    assert odoo_tools.verify_user_is_manager(0) is False
    assert odoo_tools.verify_user_is_manager(None) is False


def test_verify_manager_user_not_found(odoo_tools, monkeypatch):
    monkeypatch.setattr(odoo_tools, "_call",
                        _mock_call_factory([], [], []))
    assert odoo_tools.verify_user_is_manager(999) is False


def test_verify_manager_handles_exception(odoo_tools, monkeypatch):
    def _boom(*a, **kw):
        raise RuntimeError("XML-RPC down")
    monkeypatch.setattr(odoo_tools, "_call", _boom)
    assert odoo_tools.verify_user_is_manager(2) is False


def test_verify_manager_cache_hit(odoo_tools, monkeypatch):
    """Second call for the same user must NOT hit _call (TTL cache)."""
    calls = {"n": 0}

    def _counted(model, method, args, kwargs=None):
        calls["n"] += 1
        if model == "res.users":
            return [{"id": 5, "login": "joao", "group_ids": [31]}]
        if model == "res.groups":
            return [31]
        return []

    monkeypatch.setattr(odoo_tools, "_call", _counted)
    assert odoo_tools.verify_user_is_manager(5) is True
    n_after_first = calls["n"]
    assert odoo_tools.verify_user_is_manager(5) is True
    assert calls["n"] == n_after_first, "second call should hit the cache"
