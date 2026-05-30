from mcp_server.schemas import (
    MarketDataRequest, MarketDataResponse,
    RiskAnalysisRequest, RiskAnalysisResponse,
)
from mcp_server.audit import log_action
from db.database import SessionLocal
 
 
def get_market_data(agent_name: str, request: MarketDataRequest) -> MarketDataResponse:
    """
    Calls the real MarketAgent instead of returning random values.
    Persists the audit entry to the database.
    """
    # Import here to avoid circular imports at module load time
    from agents.market_agent import MarketAgent
 
    db = SessionLocal()
    try:
        log_action(db, agent_name, "get_market_data", request.dict())
 
        agent = MarketAgent()
        # MarketAgent.run() expects a natural-language query; build one from symbol
        result = agent.run(request.symbol)
 
        if result.get("status") == "skipped":
            raise ValueError(f"MarketAgent skipped: {result.get('reason')}")
 
        return MarketDataResponse(
            symbol=result.get("symbol", request.symbol),
            price=float(result.get("price", 0.0)),
            trend=result.get("trend", "Unknown"),
        )
    finally:
        db.close()
 
 
def analyze_risk(agent_name: str, request: RiskAnalysisRequest) -> RiskAnalysisResponse:
    """
    Calls the real RiskAgent instead of returning random volatility scores.
    Persists the audit entry to the database.
    """
    from agents.risk_agent import RiskAgent
 
    db = SessionLocal()
    try:
        log_action(db, agent_name, "analyze_risk", request.dict())
 
        agent = RiskAgent()
        result = agent.run(request.symbol)
 
        if result.get("status") == "skipped":
            raise ValueError(f"RiskAgent skipped: {result.get('reason')}")
 
        return RiskAnalysisResponse(
            symbol=result.get("instrument", request.symbol),
            risk_score=float(result.get("risk_score", 0.0)),
            volatility=result.get("volatility", "Unknown"),
        )
    finally:
        db.close()
