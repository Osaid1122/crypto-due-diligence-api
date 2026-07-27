import re
from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator
from app.core.config import SUPPORTED_CHAINS

EVM_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
SUPPORTED_EVM_CHAIN_IDS = {chain["id"] for chain in SUPPORTED_CHAINS}
# Solana addresses are base58-encoded, 32-44 characters, excluding the
# visually-ambiguous characters 0, O, I, l (standard base58 alphabet).
SOLANA_ADDRESS_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


class TokenAnalyzeRequest(BaseModel):
    address: str = Field(..., description="Token contract address (EVM) or SPL mint address (Solana)")
    chain_id: Optional[int] = Field(None, description="EVM chain ID, e.g. 1 for Ethereum, 196 for X Layer. Required when chain_type is 'evm'; ignored for Solana.")
    # Defaults to "evm" so every existing caller keeps working completely
    # unchanged — this field is new and additive, not a breaking change.
    chain_type: Literal["evm", "solana"] = "evm"

    @model_validator(mode="after")
    def validate_for_chain_type(self):
        if self.chain_type == "solana":
            if not SOLANA_ADDRESS_RE.match(self.address):
                raise ValueError("address must be a valid Solana SPL mint address (base58, 32-44 characters)")
        else:
            if self.chain_id is None:
                raise ValueError("chain_id is required when chain_type is 'evm'")
            if self.chain_id not in SUPPORTED_EVM_CHAIN_IDS:
                raise ValueError("chain_id is not supported by the configured GoPlus EVM token-security provider")
            if not EVM_ADDRESS_RE.match(self.address):
                raise ValueError("address must be a valid EVM contract address (0x + 40 hex chars)")
        return self


class TokenAnalyzeResponse(BaseModel):
    token_name: str | None = None
    token_symbol: str | None = None
    chain_type: str = "evm"
    network: str
    chain_id: int | None = None
    risk_score: int
    risk_level: str
    confidence: float = Field(..., description="Share of expected signals GoPlus actually returned (0-1)")
    confidence_known_signals: int = Field(0, description="How many expected security signals GoPlus actually returned")
    confidence_total_signals: int = Field(0, description="How many security signals we look for in total")
    summary: str
    top_concerns: list[str]
    recommended_checks: list[str]
    positive_signals: list[str] = Field(default_factory=list)
    triggered_rules: list[dict] = Field(..., description="Which rules fired and how many points each contributed")
    not_triggered_rules: list[dict] = Field(default_factory=list, description="Checks that passed cleanly — useful for demos and transparency")
    normalized_signals: dict = Field(default_factory=dict, description="Cleaned-up signal values (already computed for scoring) — for display, not re-derivation")
    technical_data: dict
