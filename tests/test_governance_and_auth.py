import datetime
import pytest
import requests
from unittest.mock import patch
from fastapi.testclient import TestClient
from jose import jwt

from api.main import app
import api.main as api_main
from api.auth import SECRET_KEY, ALGORITHM
from db.database import SessionLocal
from db.models import AuditLog
from agents.orchestrator import OrchestratorAgent
from agents.risk_agent import RiskAgent
from mcp_server.server import MCPServer

client = TestClient(app)


class FakeResp:
    def __init__(self, data, code=200):
        self._d, self.status_code = data, code
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))
    def json(self):
        return self._d


def fake_get(url, **kw):
    if "alphavantage" in url:
        return FakeResp({"Global Quote": {"05. price": "180.5", "10. change percent": "2.34%", "06. volume": "1000"}})
    return FakeResp({"chart": {"result": [{"meta": {"regularMarketPrice": 100.0, "previousClose": 98.0}}]}})


def rows_for(agent_name):
    db = SessionLocal()
    try:
        return db.query(AuditLog).filter(AuditLog.agent_name == agent_name).all()
    finally:
        db.close()


# ---------- MCP access control ----------

def test_allowed_agent_can_use_its_own_tool():
    out = MCPServer().call_tool("ComplianceAgent", "get_compliance_data", {"entity": "Tesla"})
    assert out.entity == "Tesla"


@pytest.mark.parametrize("agent,tool,payload", [
    ("ComplianceAgent", "get_market_data", {"symbol": "TSLA"}),
    ("MarketAgent", "analyze_risk", {"symbol": "AAPL"}),
    ("RandomUser", "analyze_risk", {"symbol": "AAPL"}),
    ("", "get_market_data", {"symbol": "TSLA"}),
])
def test_wrong_agent_is_denied_and_the_attempt_is_logged(agent, tool, payload):
    before = len(rows_for(agent))
    with pytest.raises(PermissionError):
        MCPServer().call_tool(agent, tool, payload)
    assert len(rows_for(agent)) == before + 1


def test_unknown_tool_is_rejected():
    with pytest.raises(ValueError):
        MCPServer().call_tool("MarketAgent", "delete_all", {})


def test_run_governed_writes_an_audit_row_and_returns_the_result_unchanged():
    before = len(rows_for("MarketAgent"))
    out = MCPServer().run_governed("MarketAgent", "get_market_data", {"query": "x"}, lambda: {"ok": 1})
    assert out == {"ok": 1}
    assert len(rows_for("MarketAgent")) == before + 1


def test_run_governed_does_not_run_the_work_for_a_denied_agent():
    called = []
    with pytest.raises(PermissionError):
        MCPServer().run_governed("RiskAgent", "get_market_data", {}, lambda: called.append(1))
    assert called == []


def test_orchestrator_audits_market_and_risk_runs():
    m, r = len(rows_for("MarketAgent")), len(rows_for("RiskAgent"))
    with patch("requests.get", side_effect=fake_get):
        OrchestratorAgent().execute("Analyze Infosys stock risk")
    assert len(rows_for("MarketAgent")) == m + 1
    assert len(rows_for("RiskAgent")) == r + 1


# ---------- JWT and login ----------

def _status(token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    with patch("requests.get", side_effect=fake_get):
        return client.post("/analyze", json={"query": "Apple stock"}, headers=headers).status_code


def test_token_without_exp_is_rejected():
    assert _status(jwt.encode({"sub": "x"}, SECRET_KEY, algorithm=ALGORITHM)) == 401


def test_expired_token_is_rejected():
    past = datetime.datetime.utcnow() - datetime.timedelta(minutes=1)
    assert _status(jwt.encode({"sub": "x", "exp": past}, SECRET_KEY, algorithm=ALGORITHM)) == 401


def test_valid_token_is_accepted():
    future = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
    assert _status(jwt.encode({"sub": "x", "exp": future}, SECRET_KEY, algorithm=ALGORITHM)) == 200


def test_login_with_configured_credentials_works_and_wrong_password_fails():
    ok = client.post("/login", json={"username": "test-admin", "password": "test-password"})
    assert ok.status_code == 200 and "access_token" in ok.json()
    assert client.post("/login", json={"username": "test-admin", "password": "nope"}).status_code == 401


def test_old_default_admin_account_no_longer_works():
    assert client.post("/login", json={"username": "admin", "password": "admin"}).status_code == 401


def test_login_is_disabled_when_credentials_are_not_configured(monkeypatch):
    monkeypatch.setattr(api_main, "_ADMIN_USERNAME", None)
    assert client.post("/login", json={"username": "a", "password": "b"}).status_code == 503


# ---------- risk agent ----------

def test_bitcoin_risk_uses_a_real_change_not_zero():
    with patch("requests.get", side_effect=fake_get):
        out = RiskAgent().run("Bitcoin risk")
    assert out["change_percent"] != 0
    assert out["data_source"].startswith("Yahoo")


def test_volatility_label_matches_the_assessment_for_a_moderate_score():
    agent = RiskAgent()
    score = agent.calculate_risk(1.5)          # 0.35
    assert score == 0.35
    with patch("requests.get", side_effect=lambda url, **kw: FakeResp(
            {"chart": {"result": [{"meta": {"regularMarketPrice": 101.5, "previousClose": 100.0}}]}})):
        out = agent.run("Infosys risk")
    assert out["volatility"] == "Medium"
    assert out["assessment"].startswith("Moderate")
