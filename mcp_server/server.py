from mcp_server.tools import get_market_data, analyze_risk, get_compliance_data
from mcp_server.schemas import (
    MarketDataRequest,
    RiskAnalysisRequest,
    ComplianceDataRequest,
)
 
 
class MCPServer:
    def __init__(self):
        self.tools = {
            "get_market_data":    get_market_data,
            "analyze_risk":       analyze_risk,
            "get_compliance_data": get_compliance_data,   # newly registered
        }
 
    def call_tool(self, agent_name: str, tool_name: str, payload: dict):
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not allowed")
 
        tool = self.tools[tool_name]
 
        if tool_name == "get_market_data":
            return tool(agent_name, MarketDataRequest(**payload))
 
        if tool_name == "analyze_risk":
            return tool(agent_name, RiskAnalysisRequest(**payload))
 
        if tool_name == "get_compliance_data":
            return tool(agent_name, ComplianceDataRequest(**payload))
