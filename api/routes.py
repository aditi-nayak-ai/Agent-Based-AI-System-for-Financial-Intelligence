import time
import threading
from collections import deque, OrderedDict

from fastapi import APIRouter, Depends, HTTPException, Request
from api.deps import get_current_user
from api.models import QueryRequest
from agents.orchestrator import OrchestratorAgent

router = APIRouter()
orchestrator = OrchestratorAgent()


@router.post("/analyze")
def analyze_financial_query(
    request: QueryRequest,
    user=Depends(get_current_user)
):
    """
    Secure endpoint for financial analysis
    """
    result = orchestrator.execute(request.query)

    return {
        "user": user["sub"],
        "result": result
    }


# ── Public demo endpoint ───────────────────────────────────────────────────────
# Lets a recruiter try the project without a login. To protect the free market
# data APIs it is limited in four ways: short queries only, a per IP limit, a
# global limit, and a short cache so repeated queries do not call the data
# sources again. The secured /analyze endpoint above is unchanged.
DEMO_MAX_QUERY_CHARS = 100
DEMO_PER_IP_PER_MIN = 6
DEMO_GLOBAL_PER_MIN = 30
DEMO_CACHE_SECONDS = 120
DEMO_CACHE_MAX_ITEMS = 200

_lock = threading.Lock()
_ip_hits: dict = {}
_global_hits: deque = deque()
_cache: OrderedDict = OrderedDict()


def reset_demo_state() -> None:
    with _lock:
        _ip_hits.clear()
        _global_hits.clear()
        _cache.clear()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _allow(hits: deque, limit: int, now: float) -> bool:
    while hits and now - hits[0] > 60:
        hits.popleft()
    if len(hits) >= limit:
        return False
    hits.append(now)
    return True


@router.post("/demo/analyze")
def demo_analyze(request: Request, body: QueryRequest):
    query = body.query.strip()
    if not query or len(query) > DEMO_MAX_QUERY_CHARS:
        raise HTTPException(
            status_code=422,
            detail=f"Query must be 1 to {DEMO_MAX_QUERY_CHARS} characters",
        )

    key = query.lower()
    now = time.time()

    with _lock:
        cached = _cache.get(key)
        if cached and now - cached[0] < DEMO_CACHE_SECONDS:
            return {"user": "demo", "cached": True, "result": cached[1]}

        ip_hits = _ip_hits.setdefault(_client_ip(request), deque())
        if len(_ip_hits) > 1000:
            for ip in [i for i, h in _ip_hits.items() if not h or now - h[-1] > 60]:
                del _ip_hits[ip]
        if not _allow(ip_hits, DEMO_PER_IP_PER_MIN, now) or not _allow(_global_hits, DEMO_GLOBAL_PER_MIN, now):
            raise HTTPException(
                status_code=429,
                detail="Demo rate limit reached. Please wait a minute and try again.",
            )

    result = orchestrator.execute(query)

    with _lock:
        _cache[key] = (time.time(), result)
        _cache.move_to_end(key)
        while len(_cache) > DEMO_CACHE_MAX_ITEMS:
            _cache.popitem(last=False)

    return {"user": "demo", "cached": False, "result": result}
