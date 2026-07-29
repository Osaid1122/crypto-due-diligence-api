from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.routers import token, wallet
from app.core.config import get_settings
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


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hackathon demo — tighten before any real deployment
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
