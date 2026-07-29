"""Request and response schemas for wallet-security analysis."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WalletAnalyzeRequest(BaseModel):
    """Inputs used to select and analyze a wallet."""

    address: str = Field(
        "",
        description="Wallet address to analyze. EVM addresses use 0x-prefixed hexadecimal; Solana addresses use base58.",
        examples=["0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"],
    )
    chain_type: str | None = Field(
        None,
        description="Optional network family override. Omit to infer the family from the address; supported values include evm, solana, and xlayer.",
        examples=["evm"],
    )


class TimelineEvent(BaseModel):
    ts: str = Field(..., description="UTC time (HH:MM) at which the analysis step was recorded.", examples=["14:32"])
    step: str = Field(..., description="Human-readable processing milestone.", examples=["Wallet validated"])


class WalletAsset(BaseModel):
    """Asset discovered in a wallet, including its token-security analysis when available."""

    model_config = ConfigDict(extra="allow")

    address: str = Field(..., description="Token contract or mint address.", examples=["0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"])
    chain_type: str = Field(..., description="Blockchain family on which the asset exists.", examples=["evm"])
    name: str = Field(..., description="Asset name reported by the provider or token analysis.", examples=["USD Coin"])
    symbol: str = Field(..., description="Asset ticker symbol.", examples=["USDC"])
    risk_score: int | float | None = Field(None, description="Token risk score from 0 to 100; null when live contract analysis is unavailable or not applicable.", examples=[18])
    risk_level: str = Field(..., description="Human-readable risk band for the asset.", examples=["Low"])
    analysis_status: str = Field(..., description="Whether token analysis succeeded, was unavailable, or was not applicable.", examples=["analyzed"])
    summary: str = Field(..., description="Concise explanation of the asset's analysis result.")
    reasons: list[str] = Field(default_factory=list, description="Risk reasons produced by triggered token-security rules.")
    has_audit: bool = Field(..., description="Whether provider data indicates an audit or open-source verification signal.", examples=[True])
    liquidity_quality: str = Field(..., description="Liquidity assessment derived from the token risk result.", examples=["Excellent"])
    technical_data: dict[str, Any] = Field(default_factory=dict, description="Provider data retained for technical inspection.")


class RiskBreakdownItem(BaseModel):
    label: str = Field(..., description="Portfolio-risk bucket label.", examples=["Low risk"])
    value: int = Field(..., description="Number of analyzed assets in this bucket.", examples=[2])


class WalletAnalyzeResponse(BaseModel):
    """Wallet analysis outcome. Error and empty outcomes retain this shape where applicable."""

    model_config = ConfigDict(extra="allow")

    status: str = Field(..., description="Analysis outcome: success, empty, or error.", examples=["success"])
    address: str = Field(..., description="Wallet address supplied for analysis.")
    chain_type: str = Field(..., description="Detected or selected blockchain family.", examples=["evm"])
    chain: str | None = Field(None, description="Compatibility alias for the chain family on error responses.")
    summary: str = Field(..., description="Plain-language summary of the wallet analysis.")
    message: str | None = Field(None, description="Additional provider or validation message, present on some error responses.")
    portfolio_score: int | None = Field(..., description="Portfolio safety score from 0 to 100; null when all assets are unscored.", examples=[82])
    risk_level: str = Field(..., description="Overall portfolio risk band.", examples=["Low"])
    timeline: list[TimelineEvent] = Field(..., description="Chronological analysis milestones.")
    assets: list[WalletAsset] = Field(..., description="Discovered assets with available token-security results.")
    risk_breakdown: list[RiskBreakdownItem] = Field(..., description="Counts of analyzed assets by risk band.")
    detail_metrics: dict[str, Any] = Field(..., description="Portfolio metrics such as asset count, audit coverage, and transaction count.")
    recommendations: list[str] = Field(..., description="Suggested follow-up checks based on the analysis.")
    balances: list[dict[str, Any]] = Field(default_factory=list, description="Raw balance records supplied by the wallet-data provider.")
    transactions: list[dict[str, Any]] = Field(default_factory=list, description="Recent transaction records supplied by the wallet-data provider.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Provider and network metadata used for the analysis.")
    error_code: str | None = Field(None, description="Machine-readable reason for an empty or error result.")
