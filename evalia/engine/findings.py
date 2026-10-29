"""Findings, evidence and the evaluator's decisions."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .documents import Document
from .verify import quote_on_page

Basis = Literal["Fact", "Interpretation"]
Action = Literal["accept", "reject", "modify"]


class Evidence(BaseModel):
    doc_id: str
    page: int
    quote: str
    verified: bool = False


class Finding(BaseModel):
    """One observation about one subject (for example a tenderer), with its evidence.

    `proposed_points` is set only for findings that feed a score. Scores are never
    proposed by a model: they are computed by code from rules the client signed off.
    """

    id: str
    subject: str
    criterion: str | None = None
    kind: str
    title: str
    detail: str
    basis: Basis
    method: str
    evidence: list[Evidence] = Field(default_factory=list)
    proposed_points: float | None = None
    severity: Literal["info", "attention", "critical"] = "info"

    @property
    def fully_verified(self) -> bool:
        return all(e.verified for e in self.evidence)


class Decision(BaseModel):
    finding_id: str
    action: Action
    reason: str = ""
    evaluator: str
    at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    modified_detail: str | None = None
    modified_points: float | None = None

    @model_validator(mode="after")
    def _reason_required(self) -> "Decision":
        if self.action != "accept" and not self.reason.strip():
            raise ValueError("a reason is required to reject or modify a finding")
        if not self.evaluator.strip():
            raise ValueError("the evaluator must be named")
        return self


def verify_evidence(finding: Finding, docs: dict[str, Document]) -> Finding:
    """Mark each piece of evidence as verified or not against its cited page.

    A finding whose evidence fails verification is kept, flagged as needing
    attention, and never presented as a Fact.
    """
    for ev in finding.evidence:
        doc = docs.get(ev.doc_id)
        ev.verified = bool(doc and quote_on_page(doc, ev.page, ev.quote))
    if finding.evidence and not finding.fully_verified:
        finding.basis = "Interpretation"
        finding.severity = "critical"
        finding.detail += " Warning: at least one quote could not be found on its cited page; check before relying on this finding."
    return finding


def final_points(finding: Finding, decision: Decision | None) -> float | None:
    """Points after review. Undecided findings carry no points into the score."""
    if finding.proposed_points is None or decision is None:
        return None
    if decision.action == "accept":
        return finding.proposed_points
    if decision.action == "reject":
        return 0.0
    return decision.modified_points if decision.modified_points is not None else finding.proposed_points
