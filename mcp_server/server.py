from mcp_server.tools import get_market_data, analyze_risk, get_compliance_data
from mcp_server.schemas import (
    MarketDataRequest,
    RiskAnalysisRequest,
    ComplianceDataRequest,
)
from mcp_server.audit import log_action
from db.database import SessionLocal

# Which agent may call which tool. Anything that is not listed here is denied.
PERMISSIONS = {
    "MarketAgent":     {"get_market_data"},
    "RiskAgent":       {"analyze_risk"},
    "ComplianceAgent": {"get_compliance_data"},
}


class MCPServer:
    def __init__(self):
        self.tools = {
            "get_market_data":     get_market_data,
            "analyze_risk":        analyze_risk,
            "get_compliance_data": get_compliance_data,
        }

    def _audit(self, agent_name: str, tool_name: str, payload: dict) -> None:
        db = SessionLocal()
        try:
            log_action(db, agent_name, tool_name, payload)
        finally:
            db.close()

    def _authorize(self, agent_name: str, tool_name: str, payload: dict) -> None:
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not allowed")
        if tool_name not in PERMISSIONS.get(agent_name, set()):
            # A denied attempt is still evidence, so it is written to the audit log.
            self._audit(agent_name, f"DENIED:{tool_name}", payload)
            raise PermissionError(f"Agent '{agent_name}' may not use tool '{tool_name}'")

    def call_tool(self, agent_name: str, tool_name: str, payload: dict):
        self._authorize(agent_name, tool_name, payload)

        tool = self.tools[tool_name]

        if tool_name == "get_market_data":
            return tool(agent_name, MarketDataRequest(**payload))

        if tool_name == "analyze_risk":
            return tool(agent_name, RiskAnalysisRequest(**payload))

        if tool_name == "get_compliance_data":
            return tool(agent_name, ComplianceDataRequest(**payload))

    def run_governed(self, agent_name: str, tool_name: str, payload: dict, fn):
        """
        Run an agent's real work under MCP control: check permission, write the
        audit row, then execute fn() and return its result unchanged.
        """
        self._authorize(agent_name, tool_name, payload)
        self._audit(agent_name, tool_name, payload)
        return fn()
