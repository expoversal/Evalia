"""Read a request for proposal into a register of requirements (`entries`), each with the page and quote it comes from.

The register is what Evalia proposes as the basis of the evaluation framework. The
client confirms or edits it, and signs it off, before any submission is opened.
This reader is deterministic and expects the structure of the fictional demo
request for proposal; a model-based reader would return the same structure.
"""
from __future__ import annotations

import re

from pydantic import BaseModel

from evalia.engine.documents import Document
from evalia.engine.verify import normalise

from .extract import money


class Entry(BaseModel):
    category: str
    key: str
    text: str
    page: int
    quote: str


class RfpFacts(BaseModel):
    doc_id: str
    reference: str = ""
    title: str = ""
    employer: str = ""
    deadline_text: str = ""
    validity_days: int | None = None
    weights: dict[str, float] = {}
    forms: list[dict] = []
    requirements: list[dict] = []
    key_roles: list[dict] = []
    boq: list[dict] = []
    provisional: dict[str, float] = {}
    particulars: dict[str, str] = {}
    entries: list[Entry] = []


def _row(row: tuple[str, ...]) -> str:
    return " ".join(c for c in row if c)


def read_rfp(doc: Document) -> RfpFacts:
    f = RfpFacts(doc_id=doc.doc_id)
    add = lambda cat, key, text, page, quote: f.entries.append(Entry(category=cat, key=key, text=text, page=page, quote=quote))  # noqa: E731
    for pg in doc.pages:
        t = normalise(pg.text)
        if m := re.search(r"Request for Proposal No\. (\S+)", t):
            f.reference = m.group(1)
            lines = [ln.strip() for ln in pg.text.splitlines() if ln.strip()]
            f.title = lines[1] if len(lines) > 1 else ""
        if m := re.search(r"Employer: (.+?\(fictional\))", t):
            f.employer = m.group(1)
            add("Context", "Employer", f.employer, pg.number, m.group(0))
        if m := re.search(r"no later than (.+? at \d\d:\d\d) local time", t):
            f.deadline_text = m.group(1)
            add("Submission", "Deadline", f"Received by {m.group(1)}; late tenders may be rejected at the Employer's discretion",
                pg.number, m.group(0))
        if m := re.search(r"remain valid for (\d+) days from the submission date", t):
            f.validity_days = int(m.group(1))
            add("Submission", "Validity", f"At least {m.group(1)} days; a shorter period is not responsive", pg.number, m.group(0))
        if m := re.search(r"The Letter of Tender shall be signed by an authorized signatory, and a power of attorney shall be provided", t):
            add("Submission", "Signature", "Letter of Tender signed, with a power of attorney for each signatory", pg.number, m.group(0))
        if m := re.search(r"Deviations or qualifications stated anywhere else in the tender shall not be considered", t):
            add("Submission", "Deviations", "Deviations only in Form G; anything stated elsewhere is not considered", pg.number, m.group(0))
        if m := re.search(r"provisional sums shall be carried at the amounts stated by the Employer", t):
            add("Commercial", "Structure", "Pricing schedules unchanged; provisional sums at the Employer's amounts", pg.number, m.group(0))
        if m := re.search(r"If the stated total is higher than the corrected sum, the tender shall be evaluated and accepted at the corrected sum", t):
            add("Commercial", "Arithmetic", "The lower of the stated and corrected totals applies", pg.number, m.group(0))
        if m := re.search(r"Technical (\d+) points; Commercial (\d+) points; Contract (\d+) points", t):
            f.weights = {"technical": float(m.group(1)), "commercial": float(m.group(2)), "contract": float(m.group(3))}
            add("Evaluation", "Weights", f"Technical {m.group(1)}, commercial {m.group(2)}, contract {m.group(3)}", pg.number, m.group(0))
        if m := re.search(r"the lowest evaluated price receives 50 points.+?divided by their own evaluated price", t):
            add("Evaluation", "Price formula", "Lowest evaluated price scores 50; others pro rata", pg.number, m.group(0))
        if m := re.search(r"2\.5 points for each hotel fit-out project.+?at most four projects are counted", t):
            add("Evaluation", "Experience", "2.5 points per qualifying hotel fit-out project, at most four", pg.number, m.group(0))
        if m := re.search(r"Provisional sums: Lot A (\$[\d,.]+); Lot B (\$[\d,.]+)", t):
            f.provisional = {"A": money(m.group(1)), "B": money(m.group(2))}
            add("Commercial", "Provisional sums", f"Lot A {m.group(1)}; Lot B {m.group(2)}", pg.number, m.group(0))
        if m := re.search(r"minimum years of relevant experience shown: (.+?)\.(?: |$)", t):
            for part in m.group(1).split("; "):
                role, years = part.rsplit(", ", 1)
                f.key_roles.append({"role": role, "years": int(years.split()[0]), "page": pg.number, "quote": part})
            add("Technical", "Key personnel", m.group(1), pg.number, m.group(0))
        for table in pg.tables:
            head = table[0] if table else ()
            if head[:3] == ("Volume", "Form", "Requirement"):
                for row in table[1:]:
                    f.forms.append({"volume": row[0], "form": row[1], "note": row[2], "page": pg.number, "quote": _row(row)})
                    add("Content", row[1], row[2] or "Required", pg.number, _row(row))
            elif head[:2] == ("Ref", "Requirement"):
                for row in table[1:]:
                    f.requirements.append({"ref": row[0], "text": row[1], "page": pg.number, "quote": _row(row)})
                    add("Requirement", row[0], row[1], pg.number, _row(row))
            elif head[:1] == ("Item",) and "Quantity Lot A" in head:
                for row in table[1:]:
                    f.boq.append({"item": row[0], "description": row[1], "unit": row[2],
                                  "qty": {"A": float(row[3].replace(",", "")), "B": float(row[4].replace(",", ""))},
                                  "page": pg.number, "quote": _row(row)})
            elif head[:2] == ("Particular", "Requirement"):
                for row in table[1:]:
                    f.particulars[row[0]] = row[1]
                    add("Contract", row[0], row[1], pg.number, _row(row))
    return f
