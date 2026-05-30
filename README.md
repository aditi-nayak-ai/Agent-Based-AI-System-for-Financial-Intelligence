# 🧠 Enterprise Agent-Based Financial Intelligence System
 
A production-architecture multi-agent AI system for financial risk analysis, compliance monitoring, and decision support — built with secure MCP tool orchestration, real-time market data, and audit-grade logging.
 
**Live Demo:** [agent-based-ai-system-for-financial.onrender.com](https://agent-based-ai-system-for-financial.onrender.com/dashboard) · **[View Source](https://github.com/aadiiiitii001/Agent-Based-AI-System-for-Financial-Intelligence)**
 
---
 
## Why This Architecture
 
Most AI demos call a single API and return a result. This system is designed around a core enterprise constraint: **in regulated environments, every AI decision must be traceable, governed, and explainable.**
 
Three design decisions reflect this:
 
**1. No agent touches tools directly.**
Every tool call — market data fetch, risk calculation, compliance lookup — routes through a central MCP Server that validates, logs, and controls access. An agent cannot bypass this layer.
 
**2. Every execution is audit-logged.**
Agent name, tool name, payload, and timestamp are persisted to the database on every request. The audit table is queryable — you can reconstruct exactly what the system did and why for any past decision.
 
**3. Risk scores are intentionally explainable.**
The volatility-based scoring (0.20 → 0.88 mapped to intraday % change bands) was chosen over a black-box ML model so a compliance officer can trace a score to a specific market movement without ML expertise. The architecture supports swapping in a trained model without changing any other layer.
 
---
 
## System Architecture
 
```
User Query → JWT Auth → Orchestrator → MCP Server → Agents → Structured Report
                                            ↓
                                       Audit Log (DB)
```
 
| Agent | Responsibility |
|---|---|
| **Orchestrator** | Parses query intent, sanitizes input, routes to relevant agents, aggregates results |
| **Risk Agent** | Fetches live price data, calculates volatility-based risk score, returns explainable assessment |
| **Compliance Agent** | Entity extraction, regulatory flag lookup, MCP-governed audit trail |
| **MCP Server** | Centralized tool registry — enforces access control, validates schemas, persists audit entries |
 
---
 
## Project Structure
 
```
finance-agent-ai/
├── agents/
│   ├── orchestrator.py       # Query routing + input sanitization
│   ├── risk_agent.py         # Live market data + risk scoring
│   ├── compliance_agent.py   # Regulatory flag detection
│   └── market_agent.py       # Price + trend data fetching
├── api/
│   ├── main.py               # FastAPI app + CORS + auth routes
│   ├── routes.py             # Protected /analyze endpoint
│   ├── auth.py               # JWT token creation + verification
│   └── deps.py               # Auth dependency injection
├── mcp_server/
│   ├── server.py             # Tool registry + call_tool() gateway
│   ├── tools.py              # Tool implementations (market, risk, compliance)
│   ├── audit.py              # DB audit log writer
│   └── schemas.py            # Pydantic request/response schemas
├── db/
│   ├── models.py             # AuditLog SQLAlchemy model
│   ├── database.py           # Engine + session factory
│   └── init_db.py            # DB initializer
├── utils/
│   ├── security.py           # Input sanitization
│   ├── text_extractor.py     # Keyword extraction for compliance
│   └── logger.py             # Structured logging
├── tests/
│   ├── test_orchestrator.py  # Mocked orchestrator tests
│   └── test_risk_agent.py    # Mocked risk agent tests
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── static/
│   └── index.html            # Live dashboard UI
├── requirements.txt
├── Procfile                  # Render deployment config
└── README.md
```
 
---
 
## Tech Stack
 
| Layer | Technology |
|---|---|
| API | FastAPI, JWT Auth, OAuth2PasswordBearer |
| Agents | Python 3.11, custom multi-agent orchestration |
| Governance | MCP Server, SQLAlchemy audit logging |
| Market Data | AlphaVantage (US stocks), Yahoo Finance (Indian stocks) |
| Database | SQLite (PostgreSQL-ready via DATABASE_URL env var) |
| DevOps | Docker, Docker Compose, Render (live) |
| Testing | Pytest, unittest.mock — no live API calls in CI |
 
---
 
## Security Design
 
- **Credentials from environment variables** — never hardcoded; startup warning emitted if defaults detected
- **CORS restricted** to known origins via `ALLOWED_ORIGINS` env var
- **Input sanitized** before reaching any agent — strips SQL injection and prompt injection characters (`;`, `--`, `/*`, `<`, `>`, null bytes)
- **JWT tokens** expire after 60 minutes
- **MCP access control** — agents declare tool calls via `call_tool()`, direct data source access is not possible
---
 
## Run Locally
 
```bash
git clone https://github.com/aadiiiitii001/Agent-Based-AI-System-for-Financial-Intelligence.git
cd Agent-Based-AI-System-for-Financial-Intelligence
```
 
Create a `.env` file:
 
```env
ALPHAVANTAGE_API_KEY=your_key_here
SECRET_KEY=sqlite:///./finance_ai.db
ADMIN_USERNAME=your_username
ADMIN_PASSWORD=your_password
ALLOWED_ORIGINS=http://localhost:8000
DATABASE_URL=sqlite:///./finance_ai.db
```
 
Install and run:
 
```bash
pip install -r requirements.txt
python db/init_db.py
uvicorn api.main:app --reload
```
 
API available at: `http://localhost:8000`
Swagger docs at: `http://localhost:8000/docs`
 
**Run with Docker:**
 
```bash
docker-compose up --build
```
 
**Run tests** (fully mocked — no API key required):
 
```bash
pytest
```
 
---
 
## Example Use Cases
 
| Query | Agents Triggered | Output |
|---|---|---|
| `Analyze Tesla stock risk` | Market + Risk | Live price, risk score, volatility band |
| `NVDA compliance check` | Compliance | Regulatory flags, audit log entry |
| `Reliance stock risk` | Market + Risk | NSE live data, INR price, risk assessment |
| `Tesla regulatory compliance` | Compliance | SEC/regulatory flags, MCP audit trail |
 
---
 
## Supported Stocks
 
**🇺🇸 US Markets (AlphaVantage)**
Tesla · Apple · NVDA · Microsoft · Amazon · Google · Meta · Netflix · Bitcoin
 
**🇮🇳 Indian Markets (Yahoo Finance — NSE/BSE)**
TCS · Infosys · Wipro · Reliance · HDFC · ICICI · HCL · Zomato · SBI · Adani · Maruti · Kotak · Bajaj · ONGC · Sun Pharma · Tech Mahindra
 
---
 
## Known Constraints & Production Roadmap
 
| Current Implementation | Production Equivalent |
|---|---|
| AlphaVantage free tier (25 req/day) | Paid data feed + Redis caching layer |
| SQLite | PostgreSQL with connection pooling |
| Single admin user | RBAC with user table and role management |
| Rule-based risk scoring | ML model trained on historical volatility (GARCH/LSTM) |
| Manual Render deployment | CI/CD pipeline with GitHub Actions |
| In-memory compliance rules | RAG pipeline over regulatory PDF documents |
 
---
 
## Screenshots
 
**Live Risk Analysis — Reliance (NSE)**
 
![Reliance Risk](https://github.com/user-attachments/assets/358e3b00-86d4-4d18-92d7-243a85e8e081)
 
**Compliance Analysis — NVDA**
 
![NVDA Compliance](https://github.com/user-attachments/assets/26ea806b-9d30-41c2-8750-48550df164cf)
 
---
 
## Author
 
**Aditi Nayak** — Software Engineer · AI & Backend Systems
 
Focused on secure, explainable AI for enterprise environments.
 
[GitHub](https://github.com/aadiiiitii001) · [Live Demo](https://agent-based-ai-system-for-financial.onrender.com/dashboard)
 
