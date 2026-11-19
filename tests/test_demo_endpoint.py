import pytest
import requests
from unittest.mock import patch
from fastapi.testclient import TestClient

from api.main import app
from api import routes

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
    return FakeResp({"chart": {"result": [{"meta": {"regularMarketPrice": 100.0, "previousClose": 98.0}}]}})


@pytest.fixture(autouse=True)
def clean_state():
    routes.reset_demo_state()
    yield
    routes.reset_demo_state()


def post(query):
    with patch("requests.get", side_effect=fake_get):
        return client.post("/demo/analyze", json={"query": query})


def test_demo_works_without_a_login():
    r = post("Analyze Infosys stock risk")
    assert r.status_code == 200
    body = r.json()
    assert body["user"] == "demo"
    assert "risk" in body["result"]["details"]


def test_secured_endpoint_still_needs_a_token():
    assert client.post("/analyze", json={"query": "Apple stock"}).status_code == 401


def test_same_query_is_served_from_cache_without_calling_the_data_source_again():
    with patch("requests.get", side_effect=fake_get) as mocked:
        first = client.post("/demo/analyze", json={"query": "Infosys stock risk"}).json()
        calls_after_first = mocked.call_count
        second = client.post("/demo/analyze", json={"query": "infosys STOCK risk"}).json()
        assert mocked.call_count == calls_after_first
    assert first["cached"] is False and second["cached"] is True


def test_per_ip_limit_returns_429():
    queries = [f"Infosys stock risk {i}" for i in range(routes.DEMO_PER_IP_PER_MIN)]
    for q in queries:
        assert post(q).status_code == 200
    assert post("TCS stock risk extra").status_code == 429


def test_cached_answers_do_not_use_up_the_limit():
    for _ in range(routes.DEMO_PER_IP_PER_MIN + 3):
        assert post("Wipro stock price").status_code == 200


@pytest.mark.parametrize("bad", ["", "   ", "x" * (routes.DEMO_MAX_QUERY_CHARS + 1)])
def test_empty_or_long_queries_are_rejected(bad):
    assert post(bad).status_code == 422
