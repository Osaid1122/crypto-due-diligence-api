import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

load_dotenv()

# CORS origins are read from ALLOWED_ORIGINS (comma-separated), falling back to
# the known production frontend domains plus the local Vite dev server. This
# replaces the previous wildcard, which allowed any site to call the API.
_DEFAULT_ALLOWED_ORIGINS = "https://cryptoduediligence.dev,https://www.cryptoduediligence.dev,http://localhost:5173"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", _DEFAULT_ALLOWED_ORIGINS).split(",")
    if origin.strip()
]

from app.routers import token, wallet
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.models.common import ServiceStatusResponse, SupportedChainsResponse

app = FastAPI(
    title="Crypto Due Diligence — Blockchain Security Intelligence API",
    description="""
Crypto Due Diligence API is a blockchain security intelligence service that helps
developers, traders, researchers, and AI agents evaluate the security of wallets,
tokens, and smart contracts across supported blockchain networks.

Features:
- Wallet security analysis
- Token security analysis
- Smart contract risk assessment
- Deterministic risk scoring
- AI-generated security explanations
- Actionable security recommendations

The API generates structured security reports by analyzing blockchain data and
security signals. Each endpoint includes documented request parameters,
response fields, and example outputs to support integration with AI agents,
applications, and blockchain security workflows.
""",
    version="1.0.0",
    openapi_tags=[
        {"name": "Token analysis", "description": "Provider-backed token and smart-contract security assessments."},
        {"name": "Wallet analysis", "description": "Live wallet portfolio discovery and explainable security assessments."},
        {"name": "Service", "description": "Service discovery, health, and supported-network endpoints."},
    ],
    contact={"name": "Crypto Due Diligence API Support"},
    license_info={"name": "Hackathon demonstration service"},
)


# Per-IP rate limiting (slowapi). The limiter instance lives in
# app.core.rate_limit so routers can import it to decorate endpoints; here we
# register it on the app, install the 429 handler, and add the middleware.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(token.router)
app.include_router(wallet.router)


@app.get(
    "/",
    tags=["Service"],
    response_model=ServiceStatusResponse,
    response_model_exclude_none=True,
    summary="Get API service information",
    description="Confirm that the Crypto Due Diligence API is reachable and identify the service.",
    responses={200: {"description": "Service is reachable.", "content": {"application/json": {"example": {"status": "ok", "service": "crypto-due-diligence-api"}}}}},
)
async def root():
    return {"status": "ok", "service": "crypto-due-diligence-api"}


@app.get(
    "/health",
    tags=["Service"],
    response_model=ServiceStatusResponse,
    response_model_exclude_none=True,
    summary="Check API health",
    description="Lightweight liveness endpoint for deployments, marketplaces, and uptime checks. It does not call external providers.",
    responses={200: {"description": "Service process is healthy.", "content": {"application/json": {"example": {"status": "healthy"}}}}},
)
async def health():
    return {"status": "healthy"}


@app.get(
    "/chains",
    tags=["Service"],
    response_model=SupportedChainsResponse,
    summary="List supported analysis networks",
    description="Return the current network configuration, including token-security and wallet-analysis availability. Use each network's `id` as `chain_id` for EVM token analysis; Solana has a null ID.",
    responses={200: {"description": "Configured analysis networks.", "content": {"application/json": {"example": {"chains": [{"key": "ethereum", "id": 1, "name": "Ethereum", "family": "evm", "address_type": "evm", "explorer": "https://etherscan.io/address/", "token_security": True, "wallet_analysis": True}]}}}}},
)
async def list_chains():
    """Single source of truth for supported chains — the frontend dropdown
    builds itself from this response instead of hardcoding options."""
    return {"chains": get_settings().analysis_networks}
