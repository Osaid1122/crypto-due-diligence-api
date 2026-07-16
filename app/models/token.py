import re
from pydantic import BaseModel, Field, field_validator

ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


class TokenAnalyzeRequest(BaseModel):
    chain_id: int = Field(..., description="EVM chain ID, e.g. 1 for Ethereum, 196 for X Layer")
    address: str = Field(..., description="Token contract address")

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        if not ADDRESS_RE.match(v):
            raise ValueError("address must be a valid EVM contract address (0x + 40 hex chars)")
        return v


class TokenAnalyzeResponse(BaseModel):
    token_name: str | None = None
    token_symbol: str | None = None
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
