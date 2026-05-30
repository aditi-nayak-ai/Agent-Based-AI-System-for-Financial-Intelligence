from pydantic import BaseModel
from typing import List
 
 
class MarketDataRequest(BaseModel):
    symbol: str
 
class MarketDataResponse(BaseModel):
    symbol: str
    price:  float
    trend:  str
 
 
class RiskAnalysisRequest(BaseModel):
    symbol: str
 
class RiskAnalysisResponse(BaseModel):
    symbol:     str
    risk_score: float
    volatility: str
 
 
class ComplianceDataRequest(BaseModel):
    entity:   str
    keywords: List[str] = []
 
class ComplianceDataResponse(BaseModel):
    entity:  str
    status:  str
    summary: str
 
