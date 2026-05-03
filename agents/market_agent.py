from mcp_server.server import MCPServer

class MarketAgent:
    def __init__(self):
        self.mcp = MCPServer()
        self.name = "MarketAgent"

    def run(self, query: str):
        symbol = "TSLA"  # extracted from query (simplified)

        response = self.mcp.call_tool(
            agent_name=self.name,
            tool_name="get_market_data",
            payload={"symbol": symbol}
        )

        return response.dict()
