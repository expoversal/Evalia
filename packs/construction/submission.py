"""Deterministic reading of a tender submission that uses the request for proposal's standard forms.

Every value read carries the page it was found on and the verbatim text it was read
from, so that each finding built on it can be checked against the page.
"""
from __future__ import annotations

import re

from pydantic import BaseModel

from evalia.engine.documents import Document
from evalia.engine.verify import normalise

from .extract import Marker, ProjectClaim, RatingEvidence, ScheduleRow, money


class Cited(BaseModel):
    text: str
    page: int
    quote: str
    tax: str | None = None


class Deviation(BaseModel):
    no: str
    particular: str
    requirement: str
    proposed: str
    reason: str
    page: int
    quote: str


class Person(BaseModel):
    role: str
    name: str
    years: int
    page: int
    quote: str


class SubmissionFacts(BaseModel):
    doc_id: str
    tenderer: str
    method: str = "form reader (deterministic)"
    pages_checked: int = 0
    letter_signed: Marker = Marker(present=False)
    validity_days: int | None = None
    validity: Cited | None = None
    offer: Cited | None = None
    letter_prices: dict[str, float] = {}
    forms: dict[str, Marker] = {}
    deviations: list[Deviation] = []
    litigation: Cited | None = None
    terminations: Cited | None = None
    collusion_signed: Marker = Marker(present=False)
    personnel: list[Person] = []
    programme_weeks: int | None = None
    programme: Cited | None = None
    subcontractors: list[Cited] = []
    methodology: list[Cited] = []
    emr: float | None = None
    emr_cited: Cited | None = None
    projects: list[ProjectClaim] = []
    ratings: list[RatingEvidence] = []
    schedules: dict[str, list[ScheduleRow]] = {}
    lot_totals: dict[str, Cited] = {}
    sum_of_lots: float | None = None
    discount_pct: float | None = None
    discount: Cited | None = None
    combined: float | None = None
    combined_cited: Cited | None = None
    cashflow: list[float] = []
    cashflow_cited: Cited | None = None
    volume_pages: dict[str, list[int]] = {}
    words: Cited | None = None
    addenda: Cited | None = None
    security_amount: float | None = None
    security_days: int | None = None
    security: Cited | None = None
    home_state: Cited | None = None
    licence: dict | None = None
    tax_certificate: dict | None = None
    turnover: list[Cited] = []
    plant: list[dict] = []
    resident_pct: float | None = None
    resident: Cited | None = None
    technical_data: dict[str, Cited] = {}
    sales_tax: Cited | None = None
    accounts: Cited | None = None
    owners: list[dict] = []
    owners_cited: Cited | None = None
    jv: list[dict] = []
    form_pages: dict[str, int] = {}
    alternative: Cited | None = None
    currencies: list[Cited] = []


def _row(row) -> str:
    return " ".join(c for c in row if c)


def _lines(pg) -> list[str]:
    return [ln.strip() for ln in pg.text.splitlines() if ln.strip()]


def read_submission(doc: Document, form_titles: list[str]) -> SubmissionFacts:
    s = SubmissionFacts(doc_id=doc.doc_id, tenderer=doc.doc_id, pages_checked=len(doc.pages))
    volume = "Volume 1"
    for pg in doc.pages:
        t, lines = normalise(pg.text), _lines(pg)
        for v in ("Volume 1", "Volume 2", "Volume 3"):
            if any(ln.startswith(v + ":") for ln in lines):
                volume = v
        s.volume_pages.setdefault(volume, []).append(pg.number)
        if m := re.search(r"Tenderer: (.+?\(fictional\))", t):
            s.tenderer = m.group(1)
        for title in form_titles:
            if title in lines and title not in s.forms:
                s.forms[title] = Marker(present=True, page=pg.number, quote=title)
        if "Volume 1: Letter of Tender" in lines:
            s.forms.setdefault("Letter of Tender", Marker(present=True, page=pg.number, quote="Volume 1: Letter of Tender"))
            if m := re.search(r"Combined Offer of (\$[\d,.]+), or for Lot A at (\$[\d,.]+) and Lot B at (\$[\d,.]+)", t):
                s.letter_prices = {"combined": money(m.group(1)), "A": money(m.group(2)), "B": money(m.group(3))}
                s.offer = Cited(text=m.group(1), page=pg.number, quote=m.group(0))
            if m := re.search(r"valid for (\d+) days from the submission date", t):
                s.validity_days = int(m.group(1))
                s.validity = Cited(text=m.group(1), page=pg.number, quote=m.group(0))
            sig = next((ln for ln in lines if ln.startswith("Signed:")), None)
            if sig and sig != "Signed:":
                s.letter_signed = Marker(present=True, page=pg.number, quote=sig)
            if m := re.search(r"Combined Offer in words: (.+?)\.", t):
                s.words = Cited(text=m.group(1), page=pg.number, quote=m.group(0))
            if m := re.search(r"We acknowledge (Addend[a-z]+ No\. \d+(?: and No\. \d+)*)", t):
                s.addenda = Cited(text=" ".join(re.findall(r"No\. (\d+)", m.group(1))), page=pg.number, quote=m.group(0))
        if "Tender Security" in lines:
            s.forms.setdefault("Tender Security", Marker(present=True, page=pg.number, quote="Tender Security"))
            a = re.search(r"Amount: (\$[\d,.]+)", t)
            v = re.search(r"This security is valid for (\d+) days from the submission date", t)
            if a and v:
                s.security_amount, s.security_days = money(a.group(1)), int(v.group(1))
                s.security = Cited(text=a.group(1), page=pg.number, quote=v.group(0))
                s.forms["Tender Security"] = Marker(present=True, page=pg.number, quote=a.group(0))
        if m := re.search(r"Site workforce resident in the State of Lakeshore: (\d+)%", t):
            s.resident_pct, s.resident = float(m.group(1)), Cited(text=m.group(1), page=pg.number, quote=m.group(0))
        if m := re.search(r"Sales tax at [\d.]+%, stated separately: \$[\d,.]+", t):
            s.sales_tax = Cited(text=m.group(0), page=pg.number, quote=m.group(0))
        if m := re.search(r"Audited accounts provided for: ([\d, ]+)\.", t):
            s.accounts = Cited(text=m.group(1), page=pg.number, quote=m.group(0))
        if m := re.search(r"Owners holding 10% or more: (.+?)\.(?: |$)", t):
            s.owners_cited = Cited(text=m.group(1), page=pg.number, quote=m.group(0))
            for part in m.group(1).split("; "):
                name, pct = part.rsplit(", ", 1)
                s.owners.append({"name": name, "pct": float(pct.rstrip("%"))})
        if any(ln.startswith("Alternative Tender") for ln in lines):
            s.alternative = Cited(text="Alternative Tender", page=pg.number, quote=next(ln for ln in lines if ln.startswith("Alternative Tender")))
        for m in re.finditer(r"(?:€|£|EUR|GBP|CAD)\s?[\d,.]+", t):
            s.currencies.append(Cited(text=m.group(0), page=pg.number, quote=m.group(0)))
        if m := re.search(r"Registered in: (.+?\(fictional\))", t):
            s.home_state = Cited(text=m.group(1), page=pg.number, quote=m.group(0))
        if m := re.search(r"General Building Contractor licence (\S+) (Class \w) (\d{1,2} \w+ \d{4})", t):
            s.licence = {"number": m.group(1), "class": m.group(2), "expiry": m.group(3), "page": pg.number, "quote": m.group(0)}
        if m := re.search(r"Tax clearance certificate (\S+) (\d{1,2} \w+ \d{4})", t):
            s.tax_certificate = {"number": m.group(1), "expiry": m.group(2), "page": pg.number, "quote": m.group(0)}
        for m in re.finditer(r"^(20\d\d) (\$[\d,]+\.\d\d)$", pg.text, re.M):
            s.turnover.append(Cited(text=m.group(2), page=pg.number, quote=m.group(0)))
        if "Form R - Anti-collusion Certificate" in lines:
            sig = next((ln for ln in lines if ln.startswith("Signed:")), None)
            s.collusion_signed = Marker(present=bool(sig and sig != "Signed:"), page=pg.number, quote=sig or "")
        if "Form O - Litigation and Arbitration" in lines:
            body = lines[lines.index("Form O - Litigation and Arbitration") + 1]
            s.litigation = Cited(text=body, page=pg.number, quote=body)
        if "Form P - Termination of Contracts" in lines:
            body = lines[lines.index("Form P - Termination of Contracts") + 1]
            s.terminations = Cited(text=body, page=pg.number, quote=body)
        if m := re.search(r"Total programme duration for both buildings: (\d+) weeks", t):
            s.programme_weeks = int(m.group(1))
            s.programme = Cited(text=m.group(1), page=pg.number, quote=m.group(0))
        if m := re.search(r"Experience Modification Rate of .+? is (\d+\.\d+)", t):
            s.emr = float(m.group(1))
            s.emr_cited = Cited(text=m.group(1), page=pg.number, quote=m.group(0))
        if "Form H - Methodology" in lines:
            for para in re.findall(r"H\.\d+ .+?(?= H\.\d+ |$)", t.split("Form H - Methodology", 1)[1].split("FICTIONAL")[0]):
                s.methodology.append(Cited(text=para.strip(), page=pg.number, quote=para.strip()))
        if "Owner Performance Evaluation" in lines:
            proj = re.search(r"^Project: (.+)$", pg.text, re.M)
            rating = re.search(r"^Overall performance rating: (.+)$", pg.text, re.M)
            if proj and rating:
                s.ratings.append(RatingEvidence(project_name=proj.group(1).strip(), rating=rating.group(1).strip(),
                                                page=pg.number, quote=rating.group(0).strip()))
        if m := re.search(r"Sum of Lot A and Lot B: (\$[\d,.]+)", t):
            s.sum_of_lots = money(m.group(1))
        if m := re.search(r"Discount for award of both lots: ([\d.]+)%", t):
            s.discount_pct = float(m.group(1))
            s.discount = Cited(text=m.group(1), page=pg.number, quote=m.group(0))
        if m := re.search(r"Combined Offer: (\$[\d,.]+)", t):
            s.combined = money(m.group(1))
            s.combined_cited = Cited(text=m.group(1), page=pg.number, quote=m.group(0))
        lot = next((x for x in ("A", "B") if f"Pricing Schedule - Lot {x}" in lines), None)
        for table in pg.tables:
            head = table[0] if table else ()
            if head[:2] == ("No.", "Particular"):
                for row in table[1:]:
                    if row[0].strip():
                        s.deviations.append(Deviation(no=row[0], particular=row[1], requirement=row[2], proposed=row[3],
                                                      reason=row[4], page=pg.number, quote=_row(row)))
            elif head[:2] == ("Role", "Name"):
                for row in table[1:]:
                    s.personnel.append(Person(role=row[0], name=row[1], years=int(row[2]), page=pg.number, quote=_row(row)))
            elif head[:2] == ("Package", "Subcontractor"):
                for row in table[1:]:
                    s.subcontractors.append(Cited(text=row[1], page=pg.number, quote=_row(row),
                                                  tax=row[2] if len(row) > 2 else None))
            elif head[:3] == ("Item", "Quantity", "Owned or leased"):
                for row in table[1:]:
                    s.plant.append({"item": row[0], "qty": int(row[1]), "owned": row[2], "page": pg.number, "quote": _row(row)})
            elif head[:2] == ("Parameter", "Offered"):
                for row in table[1:]:
                    s.technical_data[row[0]] = Cited(text=row[1], page=pg.number, quote=_row(row))
            elif head[:3] == ("Member", "Role", "Share"):
                for row in table[1:]:
                    s.jv.append({"name": row[0], "role": row[1], "pct": float(row[2].rstrip("%")), "page": pg.number, "quote": _row(row)})
            elif head[:1] == ("No.",) and "Project" in head:
                for row in table[1:]:
                    if row[0].strip().isdigit():
                        s.projects.append(ProjectClaim(
                            name=row[1], building_type=row[2], owner=row[3], completed=int(row[4]),
                            contract_value=money(row[5]) or 0.0, role=row[6], claimed_rating=row[7],
                            page=pg.number, quote=_row(row)))
            elif head[:1] == ("Item",) and lot:
                rows = s.schedules.setdefault(lot, [])
                for row in table[1:]:
                    if row[0].strip():
                        rows.append(ScheduleRow(item=row[0], description=row[1], unit=row[2],
                                                quantity=float(row[3].replace(",", "")), unit_price=money(row[4]) or 0.0,
                                                amount=money(row[5]) or 0.0, page=pg.number, quote=_row(row)))
                    elif row[1].startswith("Total Lot"):
                        s.lot_totals[lot] = Cited(text=row[5], page=pg.number, quote=_row(row))
            elif head[:1] == ("Month",):
                s.cashflow = [float(x.replace(",", "")) for x in table[1][1:]]
                s.cashflow_cited = Cited(text=f"{len(s.cashflow)} months", page=pg.number, quote=_row(table[0]))
    # Pages each form occupies: from its heading to the next form or volume heading.
    starts = sorted((m.page, title) for title, m in s.forms.items() if m.page)
    for i, (page, title) in enumerate(starts):
        nxt = next((p for p, _ in starts[i + 1:] if p > page), len(doc.pages) + 1)
        s.form_pages[title] = max(1, nxt - page)
    return s
