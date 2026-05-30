import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
 
from db.database import SessionLocal, engine
from db.models import Base
from api.routes import router
from api.auth import create_access_token
from api.models import LoginRequest
 
load_dotenv()
 
Base.metadata.create_all(bind=engine)
 
app = FastAPI(title="Enterprise Agent-Based Financial AI")
 
# ── CORS ──────────────────────────────────────────────────────────────────────
# Fix: allow_origins=["*"] was wide open in production.
# Now reads from ALLOWED_ORIGINS env var (comma-separated).
# Falls back to localhost only — never wildcards in production.
#
# In your .env file set:
#   ALLOWED_ORIGINS=https://agent-based-ai-system-for-financial.onrender.com,http://localhost:8000
#
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],   # only what the app actually uses
    allow_headers=["Authorization", "Content-Type"],
)
 
# ── Static files ───────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")
 
# ── DB session dependency ──────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
 
# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Enterprise Agent-Based Financial AI is running"}
 
# ── Dashboard ──────────────────────────────────────────────────────────────────
@app.get("/dashboard")
def dashboard():
    return FileResponse("static/index.html")
 
# ── Login ──────────────────────────────────────────────────────────────────────
# Fix 5: credentials are no longer hardcoded as "admin"/"admin".
# Read from environment variables so they can be rotated without a code change.
# Set in .env:
#   ADMIN_USERNAME=your_username
#   ADMIN_PASSWORD=your_secure_password
#
_ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
 
# Warn loudly at startup if defaults are still in use — visible in server logs
if _ADMIN_USERNAME == "admin" and _ADMIN_PASSWORD == "admin":
    import warnings
    warnings.warn(
        "WARNING: ADMIN_USERNAME and ADMIN_PASSWORD are using insecure defaults. "
        "Set them via environment variables before deploying.",
        stacklevel=1,
    )
 
@app.post("/login")
def login(data: LoginRequest):
    """
    Authenticate with credentials stored in environment variables.
    Returns a short-lived JWT on success.
    """
    if data.username == _ADMIN_USERNAME and data.password == _ADMIN_PASSWORD:
        token = create_access_token({"sub": data.username, "role": "admin"})
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")
 
# ── All other routes ───────────────────────────────────────────────────────────
app.include_router(router)
