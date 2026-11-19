"""
Live latency test for the deployed Financial Intelligence Agent.
Set the three values as environment variables first. Never type the password in the file.

  Windows PowerShell:
    $env:BASE_URL='https://YOUR-APP.onrender.com'; $env:ADMIN_USERNAME='...'; $env:ADMIN_PASSWORD='...'
  Mac or Linux:
    export BASE_URL=... ADMIN_USERNAME=... ADMIN_PASSWORD=...

Run:  python evals/live_latency.py
"""
import os, time, csv, statistics, requests

BASE = os.environ["BASE_URL"].rstrip("/")
USER, PWD = os.environ["ADMIN_USERNAME"], os.environ["ADMIN_PASSWORD"]

# Indian stocks use Yahoo (no API key limit), so they do not use up your AlphaVantage quota.
QUERIES = [
    "Analyze Infosys stock risk", "TCS stock price", "Wipro market trend", "Reliance risk assessment",
    "HDFC volatility check", "Zomato stock update", "SBI risk assessment", "Tata Motors stock price",
    "Kotak market trend", "Maruti stock risk", "ONGC stock price", "Sun Pharma risk assessment",
    "Axis Bank stock update", "Adani risk assessment", "Bajaj stock price", "Paytm market trend",
    "Tech Mahindra stock risk", "ICICI stock price", "HCL risk assessment", "Sensex market update",
]

# 1. cold start: the first call after the free Render service has been idle
t0 = time.perf_counter()
r = requests.get(BASE + "/", timeout=120)
cold = time.perf_counter() - t0
print(f"Cold start (first request): {cold:.1f} s, status {r.status_code}")

# 2. login
t0 = time.perf_counter()
resp = requests.post(BASE + "/login", json={"username": USER, "password": PWD}, timeout=60)
login_s = time.perf_counter() - t0
resp.raise_for_status()
H = {"Authorization": "Bearer " + resp.json()["access_token"]}
print(f"Login: {login_s:.2f} s")

# 3. analyze, 20 live queries
rows, times = [], []
for q in QUERIES:
    t0 = time.perf_counter()
    try:
        a = requests.post(BASE + "/analyze", json={"query": q}, headers=H, timeout=60)
        code = a.status_code
        details = a.json().get("result", {}).get("details", {}) if code == 200 else {}
    except Exception as e:
        code, details = f"error: {e}", {}
    dt = time.perf_counter() - t0
    skipped = sum(1 for v in details.values() if isinstance(v, dict) and v.get("status") == "skipped")
    rows.append([q, code, round(dt, 2), len(details), skipped])
    if code == 200:
        times.append(dt)
    time.sleep(1)  # be gentle with the data sources

ok = len(times)
times.sort()
print(f"\nSuccessful: {ok} of {len(QUERIES)}")
if ok:
    print(f"p50: {statistics.median(times):.2f} s")
    print(f"p95: {times[max(0, int(0.95 * ok) - 1)]:.2f} s")
    print(f"slowest: {times[-1]:.2f} s")
print("Queries where an agent was skipped (no data returned):", sum(1 for r in rows if r[4] > 0))

with open("live_results.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["query", "status", "seconds", "agents_run", "agents_skipped"])
    w.writerows(rows)
print("Saved live_results.csv")
