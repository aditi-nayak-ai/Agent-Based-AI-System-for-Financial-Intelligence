from agents.market_agent import MarketAgent
from agents.risk_agent import RiskAgent
from agents.compliance_agent import ComplianceAgent
from utils.security import sanitize_input
 
 
# Keywords that signal each analysis type
_MARKET_SIGNALS = {"stock", "market", "price", "trading", "shares", "analyse", "analyze"}
_RISK_SIGNALS   = {"risk", "volatility", "volatile", "analyse", "analyze", "assessment"}
_COMP_SIGNALS   = {"compliance", "regulatory", "regulation", "legal", "sec", "audit"}
 
 
class OrchestratorAgent:
    def __init__(self):
        self.market_agent     = MarketAgent()
        self.risk_agent       = RiskAgent()
        self.compliance_agent = ComplianceAgent()
 
    def plan_tasks(self, user_query: str) -> list[str]:
        """
        Derive which agents to invoke from the sanitised query.
 
        Key change from original: "Analyze Tesla risk" previously returned []
        because it contained neither "stock" nor "market". Now any of the
        broader signal sets triggers the relevant agent. When both risk and
        market signals are absent but a recognisable entity is present, we
        default to all three — better to over-report than silently skip.
        """
        tokens = set(user_query.lower().split())
        tasks: list[str] = []
 
        if tokens & _MARKET_SIGNALS:
            tasks.append("market_analysis")
        if tokens & _RISK_SIGNALS:
            tasks.append("risk_analysis")
        if tokens & _COMP_SIGNALS:
            tasks.append("compliance_check")
 
        # Fallback: if no signal matched but the query isn't empty,
        # run all three so the user gets a response rather than an error
        if not tasks and user_query.strip():
            tasks = ["market_analysis", "risk_analysis", "compliance_check"]
 
        return tasks
 
    def execute(self, raw_query: str) -> dict:
        # Fix 3: sanitize every incoming query before it reaches any agent
        user_query = sanitize_input(raw_query)
 
        plan = self.plan_tasks(user_query)
 
        if not plan:
            return {
                "summary": "No financial query detected",
                "details": {},
                "error": (
                    "Please ask about a specific stock, risk, or compliance topic. "
                    "Example: 'Analyze Tesla stock risk'"
                ),
            }
 
        results = {}
        for task in plan:
            if task == "market_analysis":
                results["market"] = self.market_agent.run(user_query)
            elif task == "risk_analysis":
                results["risk"] = self.risk_agent.run(user_query)
            elif task == "compliance_check":
                results["compliance"] = self.compliance_agent.run(user_query)
 
        return self.aggregate_results(results)
 
    def aggregate_results(self, results: dict) -> dict:
        return {
            "summary": "Automated financial intelligence report",
            "details": results,
        }
