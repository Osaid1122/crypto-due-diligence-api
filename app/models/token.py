import re
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.core.config import SUPPORTED_CHAINS

EVM_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
SUPPORTED_EVM_CHAIN_IDS = {chain["id"] for chain in SUPPORTED_CHAINS}
# Solana addresses are base58-encoded, 32-44 characters, excluding the
# visually-ambiguous characters 0, O, I, l (standard base58 alphabet).
SOLANA_ADDRESS_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


class TokenAnalyzeRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "address": "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                    "chain_type": "evm",
                    "chain_id": 1,
                },
                {
                    "address": "So11111111111111111111111111111111111111112",
                    "chain_type": "solana",
                    "chain_id": None,
                },
            ]
        }
    )
    address: str = Field(
        ...,
        description="Token contract address (EVM) or Solana SPL mint address.",
        examples=["0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"],
    )

    chain_id: Optional[int] = Field(
        None,
        description="EVM chain ID. Required when chain_type is 'evm'. Examples: 1=Ethereum, 56=BNB Chain, 137=Polygon, 196=X Layer.",
        examples=[1],
    )

    # Defaults to "evm" so every existing caller keeps working.
    chain_type: Literal["evm", "solana"] = Field(
        "evm",
        description="Blockchain type to analyze.",
        examples=["evm"],
    )

    @model_validator(mode="after")
    def validate_for_chain_type(self):
        if self.chain_type == "solana":
            if not SOLANA_ADDRESS_RE.match(self.address):
                raise ValueError(
                    "address must be a valid Solana SPL mint address (base58, 32-44 characters)"
                )
        else:
            if self.chain_id is None:
                raise ValueError(
                    "chain_id is required when chain_type is 'evm'"
                )
            if self.chain_id not in SUPPORTED_EVM_CHAIN_IDS:
                raise ValueError(
                    "chain_id is not supported by the configured GoPlus EVM token-security provider"
                )
            if not EVM_ADDRESS_RE.match(self.address):
                raise ValueError(
                    "address must be a valid EVM contract address (0x + 40 hex characters)"
                )
        return self


class TokenAnalyzeResponse(BaseModel):
    token_name: str | None = Field(None, description="Token name reported by the security provider.", examples=["USD Coin"])
    token_symbol: str | None = Field(None, description="Token ticker reported by the security provider.", examples=["USDC"])
    chain_type: str = Field("evm", description="Blockchain family used for this analysis.", examples=["evm"])
    network: str = Field(..., description="Stable key for the selected network.", examples=["ethereum"])
    chain_id: int | None = Field(None, description="EVM chain ID, or null for Solana.", examples=[1])
    risk_score: int = Field(..., description="Deterministic token risk score from 0 (lowest) to 100 (highest).", examples=[18])
    risk_level: str = Field(..., description="Human-readable band derived from the deterministic risk score.", examples=["Low"])
    max_severity: str = Field("None", description="Highest severity among the risk rules that actually fired (Critical > High > Medium > Low > Informational; 'None' when nothing triggered). Computed by the scoring engine — surfaced here so consumers use the backend's severity rather than re-deriving one.", examples=["High"])
    confidence: float = Field(..., description="Share of expected security signals returned by the provider, from 0 to 1.", examples=[0.92])
    confidence_known_signals: int = Field(0, description="Number of expected security signals returned by the provider.", examples=[23])
    confidence_total_signals: int = Field(0, description="Total number of security signals evaluated for confidence.", examples=[25])
    summary: str = Field(..., description="AI-assisted plain-language explanation of deterministic findings.")
    top_concerns: list[str] = Field(..., description="Most important security concerns identified in the analysis.")
    recommended_checks: list[str] = Field(..., description="Recommended due-diligence checks before interacting with the token.")
    positive_signals: list[str] = Field(default_factory=list, description="Positive signals observed during scoring.")
    triggered_rules: list[dict[str, Any]] = Field(..., description="Risk rules that fired, including their reasons and score impact.")
    not_triggered_rules: list[dict[str, Any]] = Field(default_factory=list, description="Security checks that did not identify a risk signal.")
    normalized_signals: dict[str, Any] = Field(default_factory=dict, description="Normalized provider signals used by the deterministic scoring engine.")
    technical_data: dict[str, Any] = Field(..., description="Unmodified technical data returned by the upstream security provider.")
