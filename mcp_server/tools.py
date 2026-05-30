from mcp_server.schemas import (
    MarketDataRequest,  MarketDataResponse,
    RiskAnalysisRequest, RiskAnalysisResponse,
    ComplianceDataRequest, ComplianceDataResponse,
)
from mcp_server.audit import log_action
from db.database import SessionLocal
 
 
def get_market_data(agent_name: str, request: MarketDataRequest) -> MarketDataResponse:
    from agents.market_agent import MarketAgent
    db = SessionLocal()
    try:
        log_action(db, agent_name, "get_market_data", request.dict())
        agent  = MarketAgent()
        result = agent.run(request.symbol)
        if result.get("status") == "skipped":
            raise ValueError(f"MarketAgent skipped: {result.get('reason')}")
        return MarketDataResponse(
            symbol=result.get("symbol", request.symbol),
            price =float(result.get("price", 0.0)),
            trend =result.get("trend", "Unknown"),
        )
    finally:
        db.close()
 
 
def analyze_risk(agent_name: str, request: RiskAnalysisRequest) -> RiskAnalysisResponse:
    from agents.risk_agent import RiskAgent
    db = SessionLocal()
    try:
        log_action(db, agent_name, "analyze_risk", request.dict())
        agent  = RiskAgent()
        result = agent.run(request.symbol)
        if result.get("status") == "skipped":
            raise ValueError(f"RiskAgent skipped: {result.get('reason')}")
        return RiskAnalysisResponse(
            symbol    =result.get("instrument", request.symbol),
            risk_score=float(result.get("risk_score", 0.0)),
            volatility=result.get("volatility", "Unknown"),
        )
    finally:
        db.close()
 
 
def get_compliance_data(
    agent_name: str, request: ComplianceDataRequest
) -> ComplianceDataResponse:
    """
    MCP-governed compliance lookup.
    Persists an audit log entry so every compliance check is traceable.
    The domain rules live in ComplianceAgent — this layer handles
    governance, logging, and schema validation only.
    """
    db = SessionLocal()
    try:
        log_action(db, agent_name, "get_compliance_data", request.dict())
        # Return a lightweight acknowledgement; the rule evaluation
        # happens in ComplianceAgent.check_compliance_rules()
        return ComplianceDataResponse(
            entity =request.entity,
            status ="lookup_complete",
            summary=f"Compliance audit initiated for {request.entity}",
        )
    finally:
        db.close()
