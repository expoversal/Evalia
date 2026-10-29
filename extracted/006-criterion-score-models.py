from pydantic import BaseModel
from typing import Literal

class Evidence(BaseModel):
    quote: str
    doc_id: str
    page: int

class CriterionScore(BaseModel):
    criterion_id: str
    score: float | None = None
    pass_fail: bool | None = None
    confidence: Literal["low", "medium", "high"]
    rationale: str
    evidence: list[Evidence]
    missing_info: list[str] = []
