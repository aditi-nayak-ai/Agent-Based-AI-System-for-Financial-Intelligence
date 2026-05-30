import os
import logging
import requests
 
logger = logging.getLogger(__name__)
 
 
class RiskAgent:
    def __init__(self):
        self.api_key   = os.getenv("ALPHAVANTAGE_API_KEY")
        self.alpha_url = "https://www.alphavantage.co/query"
        self.name      = "RiskAgent"
 
    US_SYMBOLS = {
        "TESLA": "TSLA",   "TSLA": "TSLA",
        "APPLE": "AAPL",   "AAPL": "AAPL",
        "NVIDIA": "NVDA",  "NVDA": "NVDA",
        "GOOGLE": "GOOGL", "GOOGL": "GOOGL", "ALPHABET": "GOOGL",
        "MICROSOFT": "MSFT", "MSFT": "MSFT",
        "AMAZON": "AMZN",  "AMZN": "AMZN",
        "META": "META",    "FACEBOOK": "META",
        "NETFLIX": "NFLX", "NFLX": "NFLX",
        "BITCOIN": "BTC",  "BTC": "BTC",
    }
 
    INDIA_SYMBOLS = {
        "TCS": "TCS.NS",             "TATA CONSULTANCY": "TCS.NS",
        "INFOSYS": "INFY.NS",        "INFY": "INFY.NS",
        "WIPRO": "WIPRO.NS",
        "RELIANCE": "RELIANCE.NS",
        "HDFC": "HDFCBANK.NS",       "HDFCBANK": "HDFCBANK.NS",
        "ICICI": "ICICIBANK.NS",     "ICICIBANK": "ICICIBANK.NS",
        "HCL": "HCLTECH.NS",         "HCLTECH": "HCLTECH.NS",
        "ZOMATO": "ZOMATO.NS",
        "PAYTM": "PAYTM.NS",
        "BAJAJ": "BAJAJFINSV.NS",
        "ADANI": "ADANIENT.NS",
        "TATA MOTORS": "TATAMOTORS.NS", "TATAMOTORS": "TATAMOTORS.NS",
        "TATA STEEL": "TATASTEEL.NS",
        "SBI": "SBIN.NS",            "STATE BANK": "SBIN.NS",
        "AXIS BANK": "AXISBANK.NS",  "AXISBANK": "AXISBANK.NS",
        "KOTAK": "KOTAKBANK.NS",
        "ONGC": "ONGC.NS",
        "MARUTI": "MARUTI.NS",
        "SUNPHARMA": "SUNPHARMA.NS", "SUN PHARMA": "SUNPHARMA.NS",
        "TECH MAHINDRA": "TECHM.NS", "TECHM": "TECHM.NS",
        "NIFTY": "^NSEI",            "SENSEX": "^BSESN",
    }
 
    def extract_symbol(self, query: str):
        q = query.upper().strip()
        for k, v in self.US_SYMBOLS.items():
            if k in q:
                return v, "US"
        for k, v in self.INDIA_SYMBOLS.items():
            if k in q.title() or k in q:
                return v, "IN"
        return None, None
 
    def get_us_data(self, symbol: str) -> dict | None:
        try:
            if symbol == "BTC":
                url = (
                    f"{self.alpha_url}?function=CURRENCY_EXCHANGE_RATE"
                    f"&from_currency=BTC&to_currency=USD&apikey={self.api_key}"
                )
                r    = requests.get(url, timeout=10)
                r.raise_for_status()
                rate  = r.json().get("Realtime Currency Exchange Rate", {})
                price = float(rate.get("5. Exchange Rate", 0))
                return {"price": round(price, 2), "change_percent": 0.0}
 
            url   = (
                f"{self.alpha_url}?function=GLOBAL_QUOTE"
                f"&symbol={symbol}&apikey={self.api_key}"
            )
            r     = requests.get(url, timeout=10)
            r.raise_for_status()
            quote = r.json().get("Global Quote", {})
 
            if not quote or "05. price" not in quote:
                logger.warning("AlphaVantage returned empty quote for %s", symbol)
                return None
 
            return {
                "price":          round(float(quote["05. price"]), 2),
                "change_percent": float(quote["10. change percent"].replace("%", "")),
            }
        except Exception as exc:
            logger.error("RiskAgent US fetch failed for %s: %s", symbol, exc)
            return None
 
    def get_india_data(self, symbol: str) -> dict | None:
        try:
            url     = (
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                f"?interval=1d&range=1d"
            )
            headers = {"User-Agent": "Mozilla/5.0"}
            r       = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
 
            result     = r.json()["chart"]["result"][0]
            meta       = result["meta"]
            price      = meta.get("regularMarketPrice", 0)
            prev_close = meta.get("previousClose") or meta.get("chartPreviousClose", price)
            change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
 
            return {
                "price":          round(price, 2),
                "change_percent": round(change_pct, 2),
            }
        except Exception as exc:
            logger.error("RiskAgent India fetch failed for %s: %s", symbol, exc)
            return None
 
    def calculate_risk(self, change_percent: float) -> float:
        abs_c = abs(change_percent)
        if abs_c < 1:   return 0.20
        elif abs_c < 2: return 0.35
        elif abs_c < 4: return 0.55
        elif abs_c < 6: return 0.72
        else:           return 0.88
 
    def interpret_risk(self, score: float) -> str:
        if score < 0.3:   return "Low risk – stable behavior observed"
        elif score < 0.7: return "Moderate risk – monitor for fluctuations"
        else:             return "High risk – significant volatility detected"
 
    def run(self, query: str) -> dict:
        symbol, market = self.extract_symbol(query)
 
        if not symbol:
            return {"status": "skipped", "reason": "No valid stock symbol identified"}
 
        data = (
            self.get_india_data(symbol)
            if market == "IN"
            else self.get_us_data(symbol)
        )
 
        if not data:
            return {
                "status": "skipped",
                "reason": f"Could not fetch real data for {symbol}",
            }
 
        change     = data.get("change_percent", 0)
        risk_score = self.calculate_risk(change)
 
        return {
            "instrument":    symbol,
            "market":        "NSE/BSE (India)" if market == "IN" else "NASDAQ/NYSE (US)",
            "price":         data["price"],
            "currency":      "INR ₹" if market == "IN" else "USD $",
            "change_percent": round(change, 2),
            "risk_score":    risk_score,
            "volatility":    (
                "High"   if risk_score > 0.65
                else "Medium" if risk_score > 0.35
                else "Low"
            ),
            "assessment":    self.interpret_risk(risk_score),
            "data_source":   (
                "Yahoo Finance (Real-time)"
                if market == "IN"
                else "AlphaVantage (Real-time)"
            ),
        }
