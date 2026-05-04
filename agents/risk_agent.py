import os
import re
import anthropic
import yfinance as yf
import numpy as np
 
 
SYMBOL_MAP = {
    "TESLA": "TSLA", "TSLA": "TSLA",
    "APPLE": "AAPL", "AAPL": "AAPL",
    "GOOGLE": "GOOGL", "GOOGL": "GOOGL", "ALPHABET": "GOOGL",
    "MICROSOFT": "MSFT", "MSFT": "MSFT",
    "AMAZON": "AMZN", "AMZN": "AMZN",
    "NVIDIA": "NVDA", "NVDA": "NVDA",
    "META": "META", "FACEBOOK": "META",
    "NETFLIX": "NFLX", "NFLX": "NFLX",
}
 
 
class RiskAgent:
    """
    Evaluates real financial risk using:
    - Actual price volatility from Yahoo Finance (30-day rolling std dev)
    - Claude AI for natural language risk interpretation
    """
 
    def __init__(self):
        self.name = "RiskAgent"
        # Claude client — reads ANTHROPIC_API_KEY from environment
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
 
    def extract_symbol(self, query: str) -> str:
        """
        Extract ticker symbol from natural language query.
        """
        query_upper = query.upper()
        for keyword, symbol in SYMBOL_MAP.items():
            if keyword in query_upper:
                return symbol
 
        matches = re.findall(r'\b[A-Z]{2,5}\b', query_upper)
        for match in matches:
            if match not in {"THE", "AND", "FOR", "BUY", "SELL", "WHAT", "IS", "ARE", "HOW"}:
                return match
 
        return "UNKNOWN"
 
    def calculate_volatility(self, symbol: str) -> dict:
        """
        Calculate REAL volatility from 30 days of price history.
        Uses annualized standard deviation of daily returns — standard
        financial industry method, not random numbers.
        """
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="30d")
 
        if hist.empty or len(hist) < 5:
            return {"error": f"Insufficient data for {symbol}"}
 
        # Daily returns
        closes = hist["Close"].values
        daily_returns = np.diff(closes) / closes[:-1]
 
        # Annualized volatility (industry standard)
        daily_std        = float(np.std(daily_returns))
        annualized_vol   = float(daily_std * np.sqrt(252))
 
        # Normalize to 0–1 score (cap at 100% annual vol = score of 1.0)
        risk_score = min(annualized_vol, 1.0)
 
        # Max drawdown over the period
        peak       = np.maximum.accumulate(closes)
        drawdown   = (closes - peak) / peak
        max_drawdown = float(np.min(drawdown))
 
        # Average daily volume
        avg_volume = float(hist["Volume"].mean())
 
        return {
            "symbol":          symbol,
            "risk_score":      round(risk_score, 4),
            "annualized_vol":  round(annualized_vol * 100, 2),   # as %
            "daily_std":       round(daily_std * 100, 4),         # as %
            "max_drawdown":    round(max_drawdown * 100, 2),      # as %
            "avg_volume":      int(avg_volume),
            "data_points":     len(hist),
            "current_price":   round(float(closes[-1]), 2),
            "price_30d_ago":   round(float(closes[0]), 2),
            "price_change_30d": round(((closes[-1] - closes[0]) / closes[0]) * 100, 2),
        }
 
    def get_ai_assessment(self, symbol: str, metrics: dict) -> str:
        """
        Use Claude to generate a real AI risk assessment
        based on actual calculated metrics.
        This is the line that makes it a genuine AI system.
        """
        prompt = f"""You are a financial risk analyst. Based on the following REAL market data 
for {symbol}, provide a concise 3-sentence risk assessment.
 
Data:
- Annualized Volatility: {metrics['annualized_vol']}%
- Risk Score (0-1): {metrics['risk_score']}
- Max Drawdown (30d): {metrics['max_drawdown']}%
- Price Change (30d): {metrics['price_change_30d']}%
- Current Price: ${metrics['current_price']}
- Average Daily Volume: {metrics['avg_volume']:,}
 
Provide:
1. Overall risk level (Low/Moderate/High/Extreme)
2. Key risk factors based on the numbers
3. One specific recommendation for a risk-conscious investor
 
Be direct and specific. Use the actual numbers in your response."""
 
        try:
            message = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
 
        except Exception as e:
            # Fallback to rule-based if Claude call fails
            return self.interpret_risk(metrics["risk_score"])
 
    def interpret_risk(self, risk_score: float) -> str:
        """
        Rule-based fallback if AI call fails.
        """
        if risk_score < 0.15:
            return "Low risk — annualized volatility under 15%, stable price behavior."
        elif risk_score < 0.30:
            return "Moderate risk — volatility between 15–30%, typical for large-cap equities."
        elif risk_score < 0.50:
            return "High risk — volatility between 30–50%, monitor closely."
        else:
            return "Extreme risk — annualized volatility exceeds 50%, significant drawdown potential."
 
    def run(self, query: str) -> dict:
        """
        Main method called by Orchestrator.
        """
        symbol = self.extract_symbol(query)
 
        if symbol == "UNKNOWN":
            return {
                "status": "skipped",
                "reason": "Could not identify a stock symbol in your query.",
                "hint":   "Try: 'What is the risk of TSLA?' or 'Analyze Tesla volatility'"
            }
 
        try:
            # Step 1: Calculate real volatility metrics
            metrics = self.calculate_volatility(symbol)
 
            if "error" in metrics:
                return {"status": "error", "agent": self.name, "message": metrics["error"]}
 
            # Step 2: Get AI-generated assessment from Claude
            ai_assessment = self.get_ai_assessment(symbol, metrics)
 
            return {
                "status":           "success",
                "agent":            self.name,
                "symbol":           symbol,
                "risk_score":       metrics["risk_score"],
                "annualized_vol":   f"{metrics['annualized_vol']}%",
                "max_drawdown":     f"{metrics['max_drawdown']}%",
                "price_change_30d": f"{metrics['price_change_30d']}%",
                "current_price":    metrics["current_price"],
                "data_points_used": metrics["data_points"],
                "ai_assessment":    ai_assessment,
                "method":           "real_volatility_calculation + claude_ai"
            }
 
        except Exception as e:
            return {
                "status":  "error",
                "agent":   self.name,
                "symbol":  symbol,
                "message": f"Risk calculation failed: {str(e)}"
            }
