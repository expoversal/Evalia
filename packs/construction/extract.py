"""Shared structures for what a submission states, and the model-based readers.

The deterministic form reader is in `submission.py`. The functions here send pages to
a model through the gateway; every quote a model returns is checked afterwards against
the cited page, and every value against its own quote. Arithmetic is never left to a
model.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pydantic import BaseModel, Field

from evalia.engine.documents import Document
from evalia.engine.llm import Gateway
from evalia.engine.verify import normalise

PROMPTS = Path(__file__).parent / "prompts"
_jinja = Environment(loader=FileSystemLoader(PROMPTS), undefined=StrictUndefined, autoescape=False)

MONEY = re.compile(r"\$([\d,]+(?:\.\d{2})?)")


def money(s: str) -> float | None:
    m = MONEY.search(s)
    return float(m.group(1).replace(",", "")) if m else None


class ProjectClaim(BaseModel):
    name: str
    building_type: str
    owner: str
    completed: int
    contract_value: float
    role: str
    claimed_rating: str
    page: int
    quote: str = Field(description="Verbatim text of the row or sentence that states this project")


class RatingEvidence(BaseModel):
    project_name: str
    rating: str
    page: int
    quote: str = Field(description="Verbatim sentence that states the owner's rating")


class ModelReading(BaseModel):
    """What the model is asked to return: claims and supporting evidence, never scores."""
    projects: list[ProjectClaim]
    ratings: list[RatingEvidence]
    emr: float | None = None
    emr_page: int | None = None
    emr_quote: str | None = None


class ScheduleRow(BaseModel):
    item: str
    description: str
    unit: str
    quantity: float
    unit_price: float
    amount: float
    page: int
    quote: str


class Marker(BaseModel):
    present: bool
    page: int | None = None
    quote: str | None = None


class Coverage(BaseModel):
    ref: str
    status: Literal["addressed", "not addressed", "contradicted"]
    page: int | None = None
    quote: str | None = None


class CoverageReading(BaseModel):
    """A model's mapping of the methodology against the requirements: located text, never a score."""
    items: list[Coverage]


class DeviationClass(BaseModel):
    no: str
    risk_head: str


class DeviationReading(BaseModel):
    items: list[DeviationClass]


def _pages(doc: Document) -> list[dict]:
    return [{"number": p.number, "text": p.text} for p in doc.pages]


def extract_with_model(doc: Document, gateway: Gateway) -> ModelReading:
    """A model reads the experience forms; quotes and values are checked afterwards by the pipeline."""
    prompt = _jinja.get_template("extract_bid.md.j2").render(
        pages=_pages(doc), rating_scale=["Unsatisfactory", "Marginal", "Satisfactory", "Very Good", "Exceptional"])
    return gateway.structured("construction.extract_bid", prompt, ModelReading)


def map_requirements_with_model(doc: Document, requirements: list[dict], gateway: Gateway) -> CoverageReading:
    """A model locates, for each requirement, the text that addresses or contradicts it."""
    prompt = _jinja.get_template("map_requirements.md.j2").render(pages=_pages(doc), requirements=requirements)
    return gateway.structured("construction.map_requirements", prompt, CoverageReading)


def classify_deviations_with_model(deviations: list[dict], risk_heads: list[str], gateway: Gateway) -> DeviationReading:
    """A model proposes the risk head each declared deviation falls under. The evaluator confirms it."""
    prompt = _jinja.get_template("classify_deviations.md.j2").render(deviations=deviations, risk_heads=risk_heads)
    return gateway.structured("construction.classify_deviations", prompt, DeviationReading)


def values_in_quote(claim: ProjectClaim) -> list[str]:
    """Check that the values a claim carries appear in its own quote. Returns the mismatches."""
    q = normalise(claim.quote)
    problems = []
    if str(claim.completed) not in q:
        problems.append(f"year {claim.completed} not in quote")
    if f"{claim.contract_value:,.0f}" not in q.replace(".00", ""):
        problems.append(f"value {claim.contract_value:,.0f} not in quote")
    if claim.claimed_rating not in q:
        problems.append(f"rating '{claim.claimed_rating}' not in quote")
    return problems
