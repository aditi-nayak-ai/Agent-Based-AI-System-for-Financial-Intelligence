import os
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from db.database import SessionLocal, engine
from db.models import Base
from api.routes import router
from api.auth import create_access_token
from api.models import LoginRequest

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Enterprise Agent-Based Financial AI")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

# DB session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check
@app.get("/")
def root():
    return {"message": "Enterprise Agent-Based Financial AI is running"}

# Dashboard
@app.get("/dashboard")
def dashboard():
    return FileResponse("static/index.html")

# Login
@app.post("/login")
def login(data: LoginRequest):
    if data.username == "admin" and data.password == "admin":
        token = create_access_token({"sub": data.username, "role": "admin"})
        return {"access_token": token, "token_type": "bearer"}
    return {"error": "Invalid credentials"}

# All other routes
app.include_router(router)
