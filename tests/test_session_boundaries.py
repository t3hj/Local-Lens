"""Offline regression checks for visitor isolation and council access boundaries."""
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def boundary_env(monkeypatch):
    st = SimpleNamespace(session_state={}, subheader=Mock(), warning=Mock(), info=Mock())
    factory = Mock(side_effect=lambda *_: SimpleNamespace(auth=SimpleNamespace(sign_out=Mock())))
    monkeypatch.setitem(sys.modules, "streamlit", st)
    monkeypatch.setitem(sys.modules, "supabase", SimpleNamespace(create_client=factory))
    monkeypatch.setitem(sys.modules, "config.settings", SimpleNamespace(
        SUPABASE_URL="https://example.supabase.co", SUPABASE_KEY="test-only-placeholder"))
    return st, factory


def load(path):
    return runpy.run_path(str(ROOT / path))


def test_client_reused_only_within_same_visitor(boundary_env):
    st, factory = boundary_env
    get_client = load("src/database/supabase_client.py")["get_supabase_client"]
    first_session = st.session_state
    first_client = get_client()
    assert get_client() is first_client
    st.session_state = {}
    second_client = get_client()
    assert second_client is not first_client
    st.session_state = first_session
    assert get_client() is first_client
    assert factory.call_count == 2


@pytest.mark.parametrize("signout_fails", [False, True])
def test_logout_discards_client_and_council_privileges(boundary_env, monkeypatch, signout_fails):
    st, _ = boundary_env
    get_client = load("src/database/supabase_client.py")["get_supabase_client"]
    monkeypatch.setitem(sys.modules, "src.database.supabase_client",
                        SimpleNamespace(get_supabase_client=get_client))
    service = load("src/services/auth_service.py")["AuthService"]()
    old_client = service.client
    if signout_fails:
        old_client.auth.sign_out.side_effect = RuntimeError("offline")
    st.session_state.update(ll_user="synthetic", ll_session="test-session",
                            ll_user_votes={}, council_authed=True)
    service.logout()
    assert not any(k in st.session_state for k in
                   ("ll_user", "ll_session", "ll_user_votes", "council_authed", "_ll_supabase_client"))
    assert get_client() is not old_client


@pytest.mark.parametrize("previously_authorised", [False, True])
def test_unconfigured_backup_never_calls_service(boundary_env, previously_authorised):
    st, _ = boundary_env
    st.session_state["council_authed"] = previously_authorised
    backup = Mock()
    load("src/ui/tabs/backup.py")["render_backup_tab"](backup, "")
    assert backup.mock_calls == []
    st.warning.assert_called_once()


def test_configured_backup_requires_council_login(boundary_env):
    st, _ = boundary_env
    backup = Mock()
    load("src/ui/tabs/backup.py")["render_backup_tab"](backup, "test-password")
    assert backup.mock_calls == []
    st.info.assert_called_once()


@pytest.mark.parametrize("previously_authorised", [False, True])
def test_unconfigured_insights_fail_closed(boundary_env, monkeypatch, previously_authorised):
    st, _ = boundary_env
    st.session_state["council_authed"] = previously_authorised
    scorer = Mock()
    monkeypatch.setitem(sys.modules, "pandas", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "src.services.priority_service", SimpleNamespace(score_reports=scorer))
    load("src/ui/tabs/insights.py")["render_insights_tab"]([{"id": "synthetic"}], "", Mock())
    scorer.assert_not_called()
    st.warning.assert_called_once()
