from typing import Any

from pydantic import BaseModel, Field


class InsightContract(BaseModel):
    insight_type: str
    title: str

    source_columns: list[str] = Field(default_factory=list)

    method: str

    evidence: dict[str, Any] = Field(default_factory=dict)

    calculation: dict[str, Any] = Field(default_factory=dict)

    verification: dict[str, Any] = Field(default_factory=dict)

    confidence: dict[str, Any] = Field(default_factory=dict)

    limitations: list[str] = Field(default_factory=list)
