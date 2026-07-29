"""OpenAPI models shared by application-level endpoints."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ServiceStatusResponse(BaseModel):
    """Small availability response returned by the service and health endpoints."""

    status: str = Field(..., description="Current service status.", examples=["healthy"])
    service: str | None = Field(
        None,
        description="Stable identifier for the API service. Present on the root endpoint.",
        examples=["crypto-due-diligence-api"],
    )


class SupportedChain(BaseModel):
    """A network that can be selected for token or wallet analysis."""

    model_config = ConfigDict(extra="allow")

    key: str = Field(..., description="Stable API key for the network.", examples=["ethereum"])
    id: int | None = Field(..., description="EVM chain ID, or null for Solana.", examples=[1])
    name: str = Field(..., description="Human-readable network name.", examples=["Ethereum"])
    family: str = Field(..., description="Address and analysis family used by the API.", examples=["evm"])
    address_type: str = Field(..., description="Address format expected by this network.", examples=["evm"])
    explorer: str = Field(..., description="Explorer base URL for token addresses.", examples=["https://etherscan.io/address/"])
    token_security: bool = Field(..., description="Whether token-security analysis is available.", examples=[True])
    wallet_analysis: bool = Field(..., description="Whether wallet analysis is available.", examples=[True])


class SupportedChainsResponse(BaseModel):
    chains: list[SupportedChain] = Field(
        ...,
        description="All networks currently configured for analysis.",
    )


class ProviderErrorResponse(BaseModel):
    """Standard error envelope returned when a provider request cannot be completed."""

    detail: str = Field(..., description="Human-readable explanation of the failed request.")
