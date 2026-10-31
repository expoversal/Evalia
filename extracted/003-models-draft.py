from pydantic import BaseModel, Field
from typing import Literal

class Evidence(BaseModel):
    quote: str
    doc_id: str
    page: int
    char_start: int | None = None

class CriterionScore(BaseModel):
    criterion_id: str
    score: float | None
    pass_fail: bool | None
    confidence: Literal["low","medium","high"]
    rationale: str
    evidence: list[Evidence]
    missing_info: list[str]
