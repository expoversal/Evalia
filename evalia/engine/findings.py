"""Findings, evidence and the evaluator's decisions."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .documents import Document
from .verify import quote_on_page

Basis = Literal["Fact", "Interpretation"]
Action = Literal["accept", "reject", "modify", "score"]


class Evidence(BaseModel):
    doc_id: str
    page: int
    quote: str
    verified: bool = False


class Finding(BaseModel):
    """One observation about one subject (for example a tenderer), with its evidence.

    `proposed_points` is set only for findings that feed a score. Scores are never
    proposed by a model: they are computed by code from rules the client signed off.
    Where no rule can propose points (a qualitative judgement), `score_max` is set
    instead and the evaluator gives the score, with a reason.

    `stream` groups findings into the stages of an evaluation (for example
    responsiveness, technical, commercial). `value` carries a quantity that later
    computation uses, such as an evaluated price. `clarify` holds a draft
    clarification question when the finding should be put to the tenderer.
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
    stream: str = "general"
    check: str | None = None
    score_max: float | None = None
    value: float | None = None
    clarify: str | None = None

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
    modified_value: float | None = None

    @model_validator(mode="after")
    def _reason_required(self) -> "Decision":
        if self.action != "accept" and not self.reason.strip():
            raise ValueError("a reason is required to reject, modify or score a finding")
        if self.action == "score" and self.modified_points is None:
            raise ValueError("a score is required")
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
    if decision is None:
        return None
    if decision.action == "score":
        return decision.modified_points
    if finding.proposed_points is None:
        return None
    if decision.action == "accept":
        return finding.proposed_points
    if decision.action == "reject":
        return 0.0
    return decision.modified_points if decision.modified_points is not None else finding.proposed_points


def final_value(finding: Finding, decision: Decision | None) -> float | None:
    """Value after review, for findings that carry one (such as an evaluated price)."""
    if finding.value is None or decision is None or decision.action == "reject":
        return None
    if decision.action == "modify" and decision.modified_value is not None:
        return decision.modified_value
    return finding.value
