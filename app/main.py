from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import token
from app.core.config import get_settings

app = FastAPI(
    title="Crypto Due Diligence API",
    description="A2MCP service for OKX.AI Genesis Hackathon — token risk analysis "
                 "with a deterministic scoring engine explained in plain English by AI.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hackathon demo — tighten before any real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(token.router)


@app.get("/")
async def root():
    return {"status": "ok", "service": "crypto-due-diligence-api"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/chains")
async def list_chains():
    """Single source of truth for supported chains — the frontend dropdown
    builds itself from this response instead of hardcoding options."""
    return {"chains": get_settings().supported_chains}
