"""Extract the facts a construction bid states, each with the page and quote it comes from.

Two extractors produce the same structure:

- `read_forms`: a deterministic reader for bids that use the tender's standard forms.
- `extract_with_model`: a model reads the pages, and every quote it returns is then
  checked against the cited page and against the values it claims to support.

Bid-schedule arithmetic is always read deterministically, because arithmetic is never
left to a model.
"""
from __future__ import annotations

import re
from pathlib import Path

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


class BidFacts(BaseModel):
    doc_id: str
    bidder: str
    method: str
    projects: list[ProjectClaim] = []
    ratings: list[RatingEvidence] = []
    emr: float | None = None
    emr_page: int | None = None
    emr_quote: str | None = None
    schedule: list[ScheduleRow] = []
    stated_total: float | None = None
    total_page: int | None = None
    total_quote: str | None = None
    markers: dict[str, Marker] = {}
    pages_checked: int = 0


def _bidder_name(doc: Document) -> str:
    for pg in doc.pages:
        m = re.search(r"^Bidder: (.+)$", pg.text, re.M)
        if m:
            return m.group(1).strip()
    return doc.doc_id


def _row_quote(row: tuple[str, ...]) -> str:
    return " ".join(c for c in row if c)


def read_schedule(doc: Document, facts: BidFacts) -> None:
    for pg in doc.pages:
        if "Bid Schedule" not in pg.text:
            continue
        for table in pg.tables:
            if not table or table[0][:1] != ("Item",):
                continue
            for row in table[1:]:
                if row[0].strip().isdigit():
                    facts.schedule.append(ScheduleRow(
                        item=row[0], description=row[1], unit=row[2],
                        quantity=float(row[3].replace(",", "")), unit_price=money(row[4]) or 0.0,
                        amount=money(row[5]) or 0.0, page=pg.number, quote=_row_quote(row)))
    for pg in doc.pages:
        m = re.search(r"Total base bid: (\$[\d,]+\.\d{2})", pg.text)
        if m:
            facts.stated_total, facts.total_page, facts.total_quote = money(m.group(1)), pg.number, m.group(0)
            break


def read_markers(doc: Document, facts: BidFacts, items: list[dict]) -> None:
    for item in items:
        marker = Marker(present=False)
        for pg in doc.pages:
            lines = [ln.strip() for ln in pg.text.splitlines()]
            if item.get("page_heading") and item["page_heading"] in lines:
                para = next((ln for ln in lines if ln.startswith("Principal:")), item["page_heading"])
                marker = Marker(present=True, page=pg.number, quote=para)
                break
            if item.get("marker"):
                hit = next((ln for ln in lines if item["marker"] in ln), None)
                if hit:
                    marker = Marker(present=True, page=pg.number, quote=hit)
                    break
        facts.markers[item["id"]] = marker


def read_forms(doc: Document, compliance_items: list[dict]) -> BidFacts:
    """Deterministic reading of the tender's standard forms."""
    facts = BidFacts(doc_id=doc.doc_id, bidder=_bidder_name(doc), method="form reader (deterministic)",
                     pages_checked=len(doc.pages))
    for pg in doc.pages:
        if "Statement of Experience" in pg.text:
            for table in pg.tables:
                if not table or "Project" not in table[0]:
                    continue
                for row in table[1:]:
                    if not row[0].strip().isdigit():
                        continue
                    facts.projects.append(ProjectClaim(
                        name=row[1], building_type=row[2], owner=row[3], completed=int(row[4]),
                        contract_value=money(row[5]) or 0.0, role=row[6], claimed_rating=row[7],
                        page=pg.number, quote=_row_quote(row)))
        if "Owner Performance Evaluation" in pg.text:
            proj = re.search(r"^Project: (.+)$", pg.text, re.M)
            rating = re.search(r"^Overall performance rating: (.+)$", pg.text, re.M)
            if proj and rating:
                facts.ratings.append(RatingEvidence(project_name=proj.group(1).strip(), rating=rating.group(1).strip(),
                                                    page=pg.number, quote=rating.group(0).strip()))
        m = re.search(r"Experience Modification Rate of .+? is (\d+\.\d+)", normalise(pg.text))
        if m:
            facts.emr, facts.emr_page, facts.emr_quote = float(m.group(1)), pg.number, m.group(0)
    read_schedule(doc, facts)
    read_markers(doc, facts, compliance_items)
    return facts


def extract_with_model(doc: Document, gateway: Gateway, compliance_items: list[dict]) -> BidFacts:
    """A model reads the bid; quotes and values are checked afterwards by the pipeline."""
    prompt = _jinja.get_template("extract_bid.md.j2").render(
        pages=[{"number": p.number, "text": p.text} for p in doc.pages],
        rating_scale=["Unsatisfactory", "Marginal", "Satisfactory", "Very Good", "Exceptional"])
    reading = gateway.structured("construction.extract_bid", prompt, ModelReading)
    facts = BidFacts(doc_id=doc.doc_id, bidder=_bidder_name(doc), pages_checked=len(doc.pages),
                     method=f"AI model ({gateway.profile.name}); quotes checked against pages",
                     projects=reading.projects, ratings=reading.ratings,
                     emr=reading.emr, emr_page=reading.emr_page, emr_quote=reading.emr_quote)
    read_schedule(doc, facts)
    read_markers(doc, facts, compliance_items)
    return facts


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
