from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class VerifiedEvidenceContext(BaseModel):
    """The complete, whitelisted payload that may be sent to an LLM."""

    model_config = ConfigDict(extra="forbid")

    insight_type: str
    title: str = ""
    source_columns: list[str] = Field(default_factory=list)
    method: str = ""
    evidence: dict[str, Any] = Field(default_factory=dict)
    verification: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)


class ExplanationResponse(BaseModel):
    """The only response shape accepted from an explanation provider."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
