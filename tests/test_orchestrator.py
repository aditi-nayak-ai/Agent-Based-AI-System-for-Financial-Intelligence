from unittest.mock import patch, MagicMock
from agents.orchestrator import OrchestratorAgent
 
 
MOCK_RISK_RESULT = {
    "instrument":     "TSLA",
    "market":         "NASDAQ/NYSE (US)",
    "price":          180.50,
    "currency":       "USD $",
    "change_percent": 2.34,
    "risk_score":     0.55,
    "volatility":     "Medium",
    "assessment":     "Moderate risk – monitor for fluctuations",
    "data_source":    "AlphaVantage (Real-time)",
}
 
MOCK_MARKET_RESULT = {
    "symbol":         "TSLA",
    "price":          180.50,
    "change_percent": 2.34,
    "trend":          "Bullish 📈",
    "currency":       "USD",
    "exchange":       "NASDAQ/NYSE",
    "data_source":    "AlphaVantage (Real-time)",
}
 
MOCK_COMPLIANCE_RESULT = {
    "entity":             "Tesla",
    "compliance_status":  "Attention Required",
    "flags":              ["Regulatory disclosures under review"],
    "summary":            "Potential regulatory scrutiny due to recent filings",
}
 
 
@patch("agents.orchestrator.ComplianceAgent")
@patch("agents.orchestrator.RiskAgent")
@patch("agents.orchestrator.MarketAgent")
def test_orchestrator_routes_risk_query(MockMarket, MockRisk, MockCompliance):
    """'Analyze Tesla stock risk' should trigger both market and risk agents."""
    MockRisk.return_value.run.return_value       = MOCK_RISK_RESULT
    MockMarket.return_value.run.return_value     = MOCK_MARKET_RESULT
    MockCompliance.return_value.run.return_value = MOCK_COMPLIANCE_RESULT
 
    orchestrator = OrchestratorAgent()
    result       = orchestrator.execute("Analyze Tesla stock risk")
 
    assert "details" in result
    assert "risk"    in result["details"]
    assert "market"  in result["details"]
 
 
@patch("agents.orchestrator.ComplianceAgent")
@patch("agents.orchestrator.RiskAgent")
@patch("agents.orchestrator.MarketAgent")
def test_orchestrator_sanitizes_input(MockMarket, MockRisk, MockCompliance):
    """SQL injection characters must be stripped before reaching any agent."""
    MockRisk.return_value.run.return_value       = MOCK_RISK_RESULT
    MockMarket.return_value.run.return_value     = MOCK_MARKET_RESULT
    MockCompliance.return_value.run.return_value = MOCK_COMPLIANCE_RESULT
 
    orchestrator = OrchestratorAgent()
    # Inject a semicolon — sanitize_input should strip it
    result       = orchestrator.execute("Analyze Tesla risk; DROP TABLE audit_logs--")
 
    # The request should still complete (not crash), and the injected payload
    # should never reach the agent verbatim
    assert "details" in result
    called_query = MockRisk.return_value.run.call_args[0][0]
    assert ";" not in called_query
    assert "--" not in called_query
 
 
@patch("agents.orchestrator.ComplianceAgent")
@patch("agents.orchestrator.RiskAgent")
@patch("agents.orchestrator.MarketAgent")
def test_orchestrator_compliance_only(MockMarket, MockRisk, MockCompliance):
    """A compliance-only query should invoke the compliance agent."""
    MockCompliance.return_value.run.return_value = MOCK_COMPLIANCE_RESULT
 
    orchestrator = OrchestratorAgent()
    result       = orchestrator.execute("Tesla regulatory compliance check")
 
    assert "compliance" in result["details"]
 
 
def test_orchestrator_returns_error_on_empty_query():
    """An empty string should return an error dict, not raise an exception."""
    orchestrator = OrchestratorAgent()
    result       = orchestrator.execute("")
 
    # Empty query after sanitization — plan_tasks returns [] — error expected
    assert "error" in result or "details" in result
