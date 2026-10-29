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
    security_pct: float | None = None
    security_days: int | None = None
    addenda: list[str] = []
    words_prevail: bool = False
    turnover_multiple: float | None = None
    licence_class: str | None = None
    preference_pct: float = 0.0
    home_state: str | None = None
    technical_pass: float | None = None
    methodology_cutoff: float | None = None
    standstill_days: int | None = None
    plant: list[dict] = []
    resident_pct: float | None = None
    performance: list[dict] = []
    dossier: list[dict] = []
    page_limits: dict[str, int] = {}
    negotiation: bool | None = None
    alternatives_with_base: bool = False
    sales_tax_separate: bool = False
    accounts_years: list[str] = []
    owner_threshold: float | None = None
    jv_member_min: float | None = None
    jv_lead_min: float | None = None
    subcontractor_tax: bool = False
    one_tender: bool = False
    authority_at_opening: bool = False
    headings: list[str] = []
    # Values the document states in more than one place, for the consistency check: key -> [(value, page, quote)].
    stated: dict[str, list[tuple[str, int, str]]] = {}
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
            f.stated.setdefault("Tender validity (days)", []).append((m.group(1), pg.number, m.group(0)))
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
        if m := re.search(r"tender security of not less than (\d+(?:\.\d+)?)% of the Combined Offer, valid for at least (\d+) days", t):
            f.security_pct, f.security_days = float(m.group(1)), int(m.group(2))
            f.stated.setdefault("Tender security validity (days)", []).append((m.group(2), pg.number, m.group(0)))
            add("Submission", "Tender security", f"At least {m.group(1)}% of the Combined Offer, valid for {m.group(2)} days", pg.number, m.group(0))
        if m := re.search(r"Addenda (No\. \d+(?: and No\. \d+)*) have been issued", t):
            f.addenda = re.findall(r"No\. (\d+)", m.group(1))
            add("Submission", "Addenda", f"Addenda {', '.join(f.addenda)} issued; each must be acknowledged", pg.number, m.group(0))
        if m := re.search(r"If they differ, the amount in words prevails", t):
            f.words_prevail = True
            add("Commercial", "Words and figures", "Words prevail over figures", pg.number, m.group(0))
        if m := re.search(r"The technical tender \(Volume 2\) shall contain no prices", t):
            add("Submission", "Envelopes", "No prices in the technical tender", pg.number, m.group(0))
        if m := re.search(r"General Building Contractor licence, (Class \w)", t):
            f.licence_class = m.group(1)
        if m := re.search(r"Average annual turnover over 2023 to 2025 shall be at least (\d+(?:\.\d+)?) times the Combined Offer", t):
            f.turnover_multiple = float(m.group(1))
            add("Qualification", "Eligibility", f"Contractor licence {f.licence_class}; tax clearance valid; average turnover at least "
                f"{m.group(1)} times the Combined Offer", pg.number, m.group(0))
        if m := re.search(r"not registered in the (State of \w+) is increased by (\d+(?:\.\d+)?)%", t):
            f.home_state, f.preference_pct = m.group(1), float(m.group(2))
            add("Commercial", "Domestic preference", f"{m.group(2)}% added, for comparison only, to tenderers outside the {m.group(1)}",
                pg.number, m.group(0))
        if m := re.search(r"fewer than (\d+) of the 40 technical points, or fewer than (\d+) points for methodology", t):
            f.technical_pass, f.methodology_cutoff = float(m.group(1)), float(m.group(2))
            add("Evaluation", "Technical threshold", f"At least {m.group(1)} of 40 technical points and {m.group(2)} for methodology; "
                "otherwise the commercial tender is not evaluated", pg.number, m.group(0))
        if m := re.search(r"standstill period of (\d+) days", t):
            f.standstill_days = int(m.group(1))
            add("Award", "Standstill", f"{m.group(1)} days between notification and signature", pg.number, m.group(0))
        f.headings += [ln.strip() for ln in pg.text.splitlines() if re.match(r"^\d+\. [A-Z]", ln.strip())]
        rules = [
            (r"Attendance at the site visit is mandatory", "Submission", "Site visit", "Mandatory; Site Visit Certificate required"),
            (r"Each member of a joint venture shall hold at least (\d+)% and the lead member at least (\d+)%", "Qualification",
             "Joint ventures", "Each member at least {0}%, the lead at least {1}%"),
            (r"Each named subcontractor shall provide its own tax clearance certificate", "Qualification", "Subcontractors",
             "Each subcontractor's tax clearance valid on the submission date"),
            (r"excluding sales tax, which shall be stated separately", "Commercial", "Currency and tax",
             "US dollars; sales tax stated separately"),
            (r"Alternative tenders are considered only alongside a compliant base tender", "Commercial", "Alternatives",
             "Only alongside a compliant base tender"),
            (r"Form H shall not exceed (\d+) pages", "Submission", "Page limits", "Form H at most {0} pages"),
            (r"The Employer will not negotiate with tenderers", "Award", "Negotiation", "No negotiation"),
            (r"Audited accounts for (\d{4}) to (\d{4}) shall be provided", "Qualification", "Accounts", "Audited accounts {0} to {1}"),
            (r"name every owner holding (\d+)% or more", "Qualification", "Ownership", "Owners holding {0}% or more named"),
            (r"Only one tender per tenderer will be considered", "Submission", "One tender", "One tender per tenderer"),
            (r"A representative attending the opening shall carry a letter of authority", "Submission", "Opening",
             "Representatives carry a letter of authority"),
            (r"At least (\d+)% of the site workforce shall be resident in the State of Lakeshore", "Technical", "Local workforce",
             "At least {0}% of the site workforce resident in the State"),
            (r"Minimum plant: (.+?)\.(?: |$)", "Technical", "Plant", "{0}"),
        ]
        for pat, cat, key, text in rules:
            if m := re.search(pat, t):
                add(cat, key, text.format(*m.groups()), pg.number, m.group(0))
                if key == "Joint ventures":
                    f.jv_member_min, f.jv_lead_min = float(m.group(1)), float(m.group(2))
                elif key == "Subcontractors":
                    f.subcontractor_tax = True
                elif key == "Currency and tax":
                    f.sales_tax_separate = True
                elif key == "Alternatives":
                    f.alternatives_with_base = True
                elif key == "Page limits":
                    f.page_limits["Form H - Methodology"] = int(m.group(1))
                elif key == "Negotiation":
                    f.negotiation = False
                elif key == "Accounts":
                    f.accounts_years = [str(y) for y in range(int(m.group(1)), int(m.group(2)) + 1)]
                elif key == "Ownership":
                    f.owner_threshold = float(m.group(1))
                elif key == "One tender":
                    f.one_tender = True
                elif key == "Opening":
                    f.authority_at_opening = True
                elif key == "Local workforce":
                    f.resident_pct = float(m.group(1))
                elif key == "Plant":
                    for part in m.group(1).split("; "):
                        name, qty = part.rsplit(", ", 1)
                        f.plant.append({"item": name, "qty": int(qty)})
        for table in pg.tables:
            head = table[0] if table else ()
            if head[:3] == ("Parameter", "Limit", "Value"):
                for row in table[1:]:
                    f.performance.append({"parameter": row[0], "limit": row[1], "value": float(row[2]), "page": pg.number, "quote": _row(row)})
                    add("Technical", "Performance", f"{row[0]}: {row[1]} {row[2]}", pg.number, _row(row))
            elif head[:3] == ("Annex", "Title", "Where"):
                for row in table[1:]:
                    f.dossier.append({"annex": row[0], "title": row[1], "where": row[2], "page": pg.number, "quote": _row(row)})
            if head[:3] == ("Volume", "Form", "Requirement"):
                for row in table[1:]:
                    f.forms.append({"volume": row[0], "form": row[1], "note": row[2], "page": pg.number, "quote": _row(row)})
                    for key, pat in (("Tender validity (days)", r"tender valid for (\d+) days"),
                                     ("Tender security validity (days)", r"% of the Combined Offer, valid for (\d+) days")):
                        if (mm := re.search(pat, row[2])):
                            f.stated.setdefault(key, []).append((mm.group(1), pg.number, _row(row)))
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
