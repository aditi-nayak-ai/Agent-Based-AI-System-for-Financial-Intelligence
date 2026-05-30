import os
import logging
import requests
 
logger = logging.getLogger(__name__)
 
 
class MarketAgent:
    def __init__(self):
        self.api_key  = os.getenv("ALPHAVANTAGE_API_KEY")
        self.alpha_url = "https://www.alphavantage.co/query"
        self.name     = "MarketAgent"
 
    US_SYMBOLS = {
        "TESLA": "TSLA",   "TSLA": "TSLA",
        "APPLE": "AAPL",   "AAPL": "AAPL",
        "NVIDIA": "NVDA",  "NVDA": "NVDA",
        "GOOGLE": "GOOGL", "GOOGL": "GOOGL", "ALPHABET": "GOOGL",
        "MICROSOFT": "MSFT", "MSFT": "MSFT",
        "AMAZON": "AMZN",  "AMZN": "AMZN",
        "META": "META",    "FACEBOOK": "META",
        "NETFLIX": "NFLX", "NFLX": "NFLX",
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
 
    def get_trend(self, change: float) -> str:
        if change > 1:    return "Bullish 📈"
        elif change < -1: return "Bearish 📉"
        else:             return "Neutral ➡"
 
    def get_us_data(self, symbol: str) -> dict | None:
        try:
            url = (
                f"{self.alpha_url}?function=GLOBAL_QUOTE"
                f"&symbol={symbol}&apikey={self.api_key}"
            )
            r     = requests.get(url, timeout=10)
            r.raise_for_status()
            quote = r.json().get("Global Quote", {})
 
            if not quote or "05. price" not in quote:
                logger.warning("AlphaVantage returned empty quote for %s", symbol)
                return None
 
            price  = round(float(quote["05. price"]), 2)
            change = float(quote["10. change percent"].replace("%", ""))
 
            return {
                "symbol":        symbol,
                "price":         price,
                "change_percent": round(change, 2),
                "trend":         self.get_trend(change),
                "volume":        quote.get("06. volume", "N/A"),
                "day_high":      quote.get("03. high", "N/A"),
                "day_low":       quote.get("04. low", "N/A"),
                "currency":      "USD",
                "exchange":      "NASDAQ/NYSE",
                "data_source":   "AlphaVantage (Real-time)",
            }
        except Exception as exc:
            logger.error("MarketAgent US fetch failed for %s: %s", symbol, exc)
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
 
            result = r.json()["chart"]["result"][0]
            meta   = result["meta"]
            price  = meta.get("regularMarketPrice", 0)
            prev   = meta.get("previousClose") or meta.get("chartPreviousClose", price)
            change = ((price - prev) / prev * 100) if prev else 0
 
            return {
                "symbol":         symbol,
                "price":          round(price, 2),
                "change_percent": round(change, 2),
                "trend":          self.get_trend(change),
                "volume":         meta.get("regularMarketVolume", "N/A"),
                "day_high":       meta.get("regularMarketDayHigh", "N/A"),
                "day_low":        meta.get("regularMarketDayLow", "N/A"),
                "currency":       "INR",
                "exchange":       "NSE/BSE",
                "data_source":    "Yahoo Finance (Real-time)",
            }
        except Exception as exc:
            logger.error("MarketAgent India fetch failed for %s: %s", symbol, exc)
            return None
 
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
                "reason": f"No market data available for {symbol}",
            }
 
        return data
