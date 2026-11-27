import requests
from unittest.mock import patch
 
from agents.market_agent import MarketAgent
from agents.risk_agent import RiskAgent
 
 
class FakeResp:
    def __init__(self, data, code=200):
        self._d, self.status_code = data, code
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))
    def json(self):
        return self._d
 
 
YAHOO = {"chart": {"result": [{"meta": {"regularMarketPrice": 250.0, "previousClose": 246.0}}]}}
ALPHA_OK = {"Global Quote": {"05. price": "180.50", "10. change percent": "2.34%", "06. volume": "1000"}}
ALPHA_LIMIT = {"Information": "Thank you for using Alpha Vantage. You have reached the daily rate limit."}
 
 
def make_get(alpha_body, yahoo_body=YAHOO, yahoo_code=200):
    def fake_get(url, **kw):
        if "alphavantage" in url:
            return FakeResp(alpha_body)
        return FakeResp(yahoo_body, yahoo_code)
    return fake_get
 
 
def test_market_uses_yahoo_for_a_us_stock_when_alphavantage_has_no_quota():
    with patch("requests.get", side_effect=make_get(ALPHA_LIMIT)):
        out = MarketAgent().run("Tesla stock price")
    assert out["price"] == 250.0
    assert out["currency"] == "USD" and out["exchange"] == "NASDAQ/NYSE"
    assert out["data_source"].startswith("Yahoo")
 
 
def test_risk_uses_yahoo_for_a_us_stock_when_alphavantage_has_no_quota():
    with patch("requests.get", side_effect=make_get(ALPHA_LIMIT)):
        out = RiskAgent().run("Tesla risk")
    assert out["risk_score"] == 0.35
    assert out["currency"] == "USD $"
    assert out["data_source"].startswith("Yahoo")
 
 
def test_alphavantage_is_still_used_first_when_it_works():
    with patch("requests.get", side_effect=make_get(ALPHA_OK)):
        market = MarketAgent().run("Tesla stock price")
        risk = RiskAgent().run("Tesla risk")
    assert market["price"] == 180.5 and market["data_source"].startswith("AlphaVantage")
    assert risk["data_source"].startswith("AlphaVantage")
 
 
def test_when_both_sources_fail_the_result_is_skipped_not_a_crash():
    with patch("requests.get", side_effect=make_get(ALPHA_LIMIT, {}, 500)):
        assert MarketAgent().run("Tesla stock price")["status"] == "skipped"
        assert RiskAgent().run("Tesla risk")["status"] == "skipped"
