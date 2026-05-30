from unittest.mock import patch, MagicMock
from agents.risk_agent import RiskAgent
 
 
MOCK_ALPHAVANTAGE_RESPONSE = {
    "Global Quote": {
        "01. symbol":             "TSLA",
        "05. price":              "180.50",
        "10. change percent":     "2.34%",
        "06. volume":             "95000000",
        "03. high":               "183.00",
        "04. low":                "178.00",
    }
}
 
 
@patch("agents.risk_agent.requests.get")
def test_risk_agent_returns_expected_fields(mock_get):
    """Agent returns all required keys when AlphaVantage responds correctly."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = MOCK_ALPHAVANTAGE_RESPONSE
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp
 
    agent    = RiskAgent()
    response = agent.run("Analyze TSLA risk")
 
    assert "risk_score"  in response, "risk_score missing"
    assert "assessment"  in response, "assessment missing"
    assert "volatility"  in response, "volatility missing"
    assert "instrument"  in response, "instrument missing"
    assert isinstance(response["risk_score"], float)
    assert 0.0 <= response["risk_score"] <= 1.0
 
 
@patch("agents.risk_agent.requests.get")
def test_risk_agent_handles_empty_api_response(mock_get):
    """Agent returns a skipped status gracefully when the API returns nothing."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"Global Quote": {}}
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp
 
    agent    = RiskAgent()
    response = agent.run("Analyze TSLA risk")
 
    assert response.get("status") == "skipped"
    assert "reason" in response
 
 
def test_risk_agent_handles_unknown_symbol():
    """Agent returns skipped when no recognisable symbol is in the query."""
    agent    = RiskAgent()
    response = agent.run("What is the weather today")
 
    assert response.get("status") == "skipped"
 
 
@patch("agents.risk_agent.requests.get")
def test_risk_score_high_volatility(mock_get):
    """A 7% daily change should produce a risk score of 0.88 (high band)."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "Global Quote": {
            "05. price":          "200.00",
            "10. change percent": "7.00%",
        }
    }
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp
 
    agent    = RiskAgent()
    response = agent.run("Analyze TSLA risk")
 
    assert response.get("risk_score") == 0.88
    assert response.get("volatility") == "High"
