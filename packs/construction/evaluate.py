"""The construction pack's checks, stream by stream, from receipt to integrity.

Each check turns facts read from the request for proposal and the submissions into
findings with cited evidence. Points are proposed only where a signed-off rule gives
them; qualitative judgements are left to the evaluator. Cross-tender comparisons
(price scores, outliers, identical rates) use the industry-neutral engine functions.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel

from evalia.engine.documents import Document
from evalia.engine.findings import Evidence, Finding, verify_evidence
from evalia.engine.rules import BandRule, RecordRule
from evalia.engine.scoring import (apply_correction_rule, cheapest_award, deviations_from_median, front_loading,
                                   identical_values)
from evalia.engine.verify import normalise

from .extract import values_in_quote
from .rfp import RfpFacts
from .submission import SubmissionFacts

FRAMEWORK_FILE = Path(__file__).parent / "framework.yaml"


class Framework(BaseModel):
    award_basis: str
    correction_rule: str
    streams: list[dict]
    criteria: list[dict]
    record_rule: RecordRule
    band_rules: list[BandRule]
    technical_forms: list[str]
    risk_heads: dict[str, dict]
    deduction: dict[str, float]
    qualification_phrases: list[str]
    requirement_keywords: dict[str, list[list[str]]]
    numeric_requirements: dict[str, dict]
    thresholds: dict[str, float]
    pre_tender_estimate: float | None = None
    sensitivity: dict[str, dict[str, float]]
    not_assessed: list[str]


def load_framework() -> Framework:
    return Framework.model_validate(yaml.safe_load(FRAMEWORK_FILE.read_text()))


def _usd(x: float) -> str:
    return f"${x:,.2f}"


def _key(name: str) -> str:
    return normalise(name).lower()


class _Sink:
    """Collects findings for one tenderer, numbering them and checking every quote against its page."""

    def __init__(self, key: str, subject: str, docs: dict[str, Document], method: str, out: list[Finding]):
        self.key, self.subject, self.docs, self.method, self.out, self.n = key, subject, docs, method, out, 0

    def add(self, stream: str, **kw) -> Finding:
        self.n += 1
        kw.setdefault("method", self.method)
        f = verify_evidence(Finding(id=f"{self.key}-{self.n:02d}", subject=self.subject, stream=stream, **kw), self.docs)
        self.out.append(f)
        return f


def ev(doc_id: str, page: int | None, quote: str | None) -> list[Evidence]:
    return [Evidence(doc_id=doc_id, page=page or 0, quote=quote or "")] if quote else []


# --- Receipt and responsiveness -------------------------------------------------------------------------------------

def check_receipt(s: SubmissionFacts, sink: _Sink, received: str | None, deadline: str) -> None:
    if not received:
        sink.add("receipt", kind="receipt", basis="Fact", check="Receipt time", title="Receipt time not recorded",
                 detail="The opening record has no receipt time for this submission.", severity="attention", method="opening record")
        return
    late = (datetime.fromisoformat(received) - datetime.fromisoformat(deadline)).total_seconds() / 60
    when = datetime.fromisoformat(received).strftime("%d %B %Y at %H:%M").lstrip("0")
    if late > 0:
        sink.add("receipt", kind="receipt", basis="Fact", check="Receipt time", title=f"Received {late:.0f} minutes after the deadline",
                 detail=f"The portal recorded receipt on {when}. Under the request for proposal, late tenders may be rejected "
                        "at the Employer's discretion: the panel must decide whether to open it.",
                 severity="critical", method="opening record",
                 clarify=None)
    else:
        sink.add("receipt", kind="receipt", basis="Fact", check="Receipt time", title="Received before the deadline",
                 detail=f"The portal recorded receipt on {when}.", method="opening record")


def check_gate(rfp: RfpFacts, s: SubmissionFacts, doc: Document, sink: _Sink, fw: Framework) -> None:
    d = doc.doc_id
    if s.letter_signed.present:
        sink.add("gate", kind="presence", basis="Fact", check="Letter of Tender signed", title="Letter of Tender signed", detail="Signed by a named signatory.",
                 evidence=ev(d, s.letter_signed.page, s.letter_signed.quote))
    else:
        sink.add("gate", kind="presence", basis="Fact", check="Letter of Tender signed", title="Letter of Tender not signed",
                 detail=f"No signature found on the Letter of Tender ({s.pages_checked} pages checked).", severity="critical",
                 clarify="Please confirm who signed the Letter of Tender and provide a signed copy.")
    poa = s.forms.get("Power of Attorney")
    if poa:
        sink.add("gate", kind="presence", basis="Fact", check="Power of attorney", title="Power of attorney provided", detail="Found in Volume 1.",
                 evidence=ev(d, poa.page, poa.quote))
    else:
        sink.add("gate", kind="presence", basis="Fact", check="Power of attorney", title="Power of attorney not found",
                 detail=f"The request for proposal requires a power of attorney for each signatory. None was found "
                        f"({s.pages_checked} pages checked).", severity="critical",
                 clarify="Please provide the power of attorney authorizing the signatory of the Letter of Tender.")
    if s.validity_days is not None and rfp.validity_days is not None:
        short = s.validity_days < rfp.validity_days
        sink.add("gate", kind="threshold", basis="Fact",
                 check="Validity period", title=f"Validity {s.validity_days} days" + (f", shorter than the {rfp.validity_days} required" if short else ""),
                 detail=(f"The request for proposal requires {rfp.validity_days} days and states that a shorter period "
                         "shall be rejected as not substantially responsive." if short
                         else f"Meets the {rfp.validity_days} days required."),
                 evidence=ev(d, s.validity.page, s.validity.quote), severity="critical" if short else "info",
                 clarify=(f"Please confirm whether you extend the validity of your tender to {rfp.validity_days} days."
                          if short else None))
    required = [f["form"] for f in rfp.forms if f["form"] not in ("Letter of Tender", "Power of Attorney")]
    missing = [f for f in required if f not in s.forms]
    sink.add("gate", kind="set", basis="Fact",
             check="Required forms", title=f"{len(required) - len(missing)} of {len(required)} required forms present",
             detail=("Every required form was found." if not missing else "Missing: " + "; ".join(missing) + "."),
             severity="critical" if missing else "info",
             clarify=("Please submit: " + "; ".join(missing) + ".") if missing else None)
    for lot in ("A", "B"):
        rows = s.schedules.get(lot, [])
        issued = {(b["item"], b["description"], b["qty"][lot]) for b in rfp.boq}
        priced = {(r.item, r.description, r.quantity) for r in rows}
        changed = sorted(issued ^ priced)
        sink.add("gate", kind="set", basis="Fact",
                 check="Pricing schedule structure", title=f"Pricing schedule, Lot {lot}: " + ("structure as issued" if not changed else "structure changed"),
                 detail=("Every item and quantity matches the schedule issued with the request for proposal." if not changed
                         else "Items or quantities differ from the issued schedule: " + "; ".join(f"{i} {t}" for i, t, _ in changed) + "."),
                 evidence=ev(d, rows[0].page, rows[0].quote) if rows else [], severity="critical" if changed else "info")
        ps = next((r for r in rows if r.unit == "PS"), None)
        want = rfp.provisional.get(lot)
        if ps and want is not None and abs(ps.amount - want) > 0.01:
            sink.add("gate", kind="threshold", basis="Fact",
                     check="Provisional sums", title=f"Provisional sum, Lot {lot}: {_usd(ps.amount)} instead of {_usd(want)}",
                     detail="Provisional sums must be carried at the Employer's amounts. The commercial evaluation normalises "
                            f"the price by adding back {_usd(want - ps.amount)}.",
                     evidence=ev(d, ps.page, ps.quote), severity="attention",
                     clarify=f"Please confirm that the provisional sum for Lot {lot} is carried at {_usd(want)}.")
    priced = [x for x in ("A", "B") if s.lot_totals.get(x)] + (["combined offer"] if s.combined else [])
    sink.add("gate", kind="set", basis="Fact", check="All lots priced", title=f"Priced: Lot A, Lot B and combined offer" if len(priced) == 3 else "Not every lot priced",
             detail="Both lots and the combined offer are priced." if len(priced) == 3 else f"Priced only: {', '.join(priced)}.",
             evidence=ev(d, s.combined_cited.page, s.combined_cited.quote) if s.combined_cited else [],
             severity="info" if len(priced) == 3 else "critical")
    if s.collusion_signed.present:
        sink.add("gate", kind="presence", basis="Fact", check="Anti-collusion certificate", title="Anti-collusion certificate signed", detail="Form R is signed.",
                 evidence=ev(d, s.collusion_signed.page, s.collusion_signed.quote))
    else:
        sink.add("gate", kind="presence", basis="Fact", check="Anti-collusion certificate", title="Anti-collusion certificate not signed",
                 detail="Form R is present but unsigned, or missing.", severity="critical",
                 clarify="Please provide a signed anti-collusion certificate (Form R).")
    form_g = s.forms.get("Form G - Proposed Changes to Tender Requirements")
    for pg in doc.pages:
        if form_g and pg.number == form_g.page:
            continue
        for sentence in re.split(r"(?<=\.)\s+", normalise(pg.text)):
            if any(ph in sentence.lower() for ph in fw.qualification_phrases) and "FICTIONAL" not in sentence:
                sink.add("gate", kind="qualification", basis="Interpretation",
                         check="Qualifications outside Form G", title="Possible qualification stated outside Form G",
                         detail="This sentence reads as an assumption or exclusion, but it is not in Form G. Under the request for "
                                "proposal it is not considered, so the tenderer is held to the requirements as written. Ask the "
                                "tenderer to confirm or withdraw it, because it may explain part of the price.",
                         evidence=ev(d, pg.number, sentence), severity="attention", method="phrase search (deterministic)",
                         clarify=f"Your tender states: \"{sentence}\" Qualifications outside Form G are not considered. "
                                 "Please confirm that your price is not conditional on it.")


# --- Technical ------------------------------------------------------------------------------------------------------

def check_technical(rfp: RfpFacts, s: SubmissionFacts, doc: Document, sink: _Sink, fw: Framework) -> dict:
    d = doc.doc_id
    missing = [f for f in fw.technical_forms if f not in s.forms]
    sink.add("technical", criterion="T1", kind="set", basis="Fact",
             check="T1 Quality of submission", title=f"Quality of submission: {len(fw.technical_forms) - len(missing)} of {len(fw.technical_forms)} technical forms",
             detail="Every technical form is present." if not missing else "Missing: " + "; ".join(missing) + ".",
             proposed_points=float(-len(missing)), severity="info" if not missing else "attention")

    # Methodology: requirement coverage, then the evaluator's score.
    coverage = {}
    for req in rfp.requirements:
        ref = req["ref"]
        hit = None
        groups = fw.requirement_keywords.get(ref, [])
        num = fw.numeric_requirements.get(ref)
        if num and num.get("source") == "programme_weeks" and s.programme:
            ok = s.programme_weeks <= num["max"]
            coverage[ref] = "addressed" if ok else "contradicted"
            hit = (s.programme.page, s.programme.quote)
        elif groups:
            for para in s.methodology:
                low = para.text.lower()
                if all(any(k.lower() in low for k in g) for g in groups):
                    hit = (para.page, para.quote)
                    break
            coverage[ref] = "addressed" if hit else "not addressed"
            if hit and num and (m := re.search(num["pattern"], normalise(hit[1]))) and float(m.group(1)) < num["min"]:
                coverage[ref] = "contradicted"
        else:
            coverage[ref] = "not addressed"
        status = coverage[ref]
        sink.add("technical", criterion="T2", kind="coverage", basis="Interpretation",
                 method="keyword matcher (prototype stand-in for a model reading)",
                 check=f"T2 {ref}", title=f"{ref}: {'addressed' if status == 'addressed' else 'not demonstrated' if status == 'not addressed' else 'conflicts with the requirement'}",
                 detail=f"Requirement: {req['text']}" + ("" if status == "addressed" else
                        " The methodology does not show how this will be met." if status == "not addressed" else
                        " The submission states something that does not meet it."),
                 evidence=ev(d, *hit) if hit else [],
                 severity="info" if status == "addressed" else "attention" if status == "not addressed" else "critical",
                 clarify=(None if status == "addressed" else f"Please explain how your methodology meets {ref}: {req['text']}"))
    gaps = [r for r, st in coverage.items() if st != "addressed"]
    sink.add("technical", criterion="T2", kind="judgement", basis="Interpretation", method="evaluator",
             check="T2 Methodology score", title="Methodology: evaluator's score",
             detail=f"{len(coverage) - len(gaps)} of {len(coverage)} requirements are addressed in the methodology"
                    + (f"; not demonstrated or in conflict: {', '.join(gaps)}." if gaps else ".")
                    + " Evalia does not propose a score for methodology: the evaluator scores it, with a reason.",
             score_max=10.0, severity="attention" if gaps else "info")

    band = {b.id: b for b in fw.band_rules}
    if s.programme_weeks is not None:
        pts = band["T3"].points_for(s.programme_weeks)
        sink.add("technical", criterion="T3", kind="band", basis="Fact", check="T3 Programme", title=f"Programme: {s.programme_weeks} weeks",
                 detail=f"{s.programme_weeks} weeks against the 40 required; worth {pts:g} of {band['T3'].max_points:g} points.",
                 evidence=ev(d, s.programme.page, s.programme.quote), proposed_points=pts,
                 severity="info" if s.programme_weeks <= 40 else "critical")
    if s.emr is not None:
        pts = band["T4"].points_for(s.emr)
        sink.add("technical", criterion="T4", kind="band", basis="Fact", check="T4 Health and safety", title=f"Experience Modification Rate: {s.emr:.2f}",
                 detail=f"Certified rate {s.emr:.2f} is in the band worth {pts:g} of {band['T4'].max_points:g} points.",
                 evidence=ev(d, s.emr_cited.page, s.emr_cited.quote), proposed_points=pts,
                 severity="info" if pts == band["T4"].max_points else "attention")

    rule = fw.record_rule
    ratings = {_key(r.project_name): r for r in s.ratings}
    for pr in s.projects:
        e = ev(d, pr.page, pr.quote)
        letter = ratings.get(_key(pr.name))
        if letter:
            e += ev(d, letter.page, letter.quote)
        record = {rule.keyword_field: pr.building_type, rule.year_field: pr.completed, rule.value_field: pr.contract_value,
                  rule.role_field: pr.role, rule.rating_field: letter.rating if letter else None}
        reasons = rule.check(record) + (["values do not match the quoted text"] if values_in_quote(pr) else [])
        ok = not reasons
        sink.add("technical", criterion="T5", kind="record", basis="Fact",
                 check="T5 Relevant experience", title=f"{pr.name}: {'counts' if ok else 'does not count'} as relevant experience",
                 detail="Meets every condition of the signed-off rule." if ok else "Fails: " + "; ".join(reasons) + ".",
                 evidence=e, proposed_points=rule.points_per_record if ok else 0.0, severity="info" if ok else "attention")
        if letter and letter.rating != pr.claimed_rating:
            sink.add("technical", criterion="T5", kind="substantiation", basis="Fact",
                     check="T5 Claims substantiated", title=f"{pr.name}: claimed rating not substantiated",
                     detail=f"Form K claims '{pr.claimed_rating}'; the owner's own evaluation, attached to the same tender, gives "
                            f"'{letter.rating}'. The owner's rating has been used."
                            + (f" Relying on the claim would have added {rule.points_per_record:g} points."
                               if not rule.check({**record, rule.rating_field: pr.claimed_rating}) and reasons else ""),
                     evidence=e, severity="critical",
                     clarify=f"Form K states an owner rating of '{pr.claimed_rating}' for {pr.name}, but the attached evaluation "
                             f"states '{letter.rating}'. Please explain the difference.")

    named = {p.role: p for p in s.personnel}
    for kr in rfp.key_roles:
        p = named.get(kr["role"])
        ok = bool(p and p.years >= kr["years"])
        sink.add("technical", criterion="T6", kind="threshold", basis="Fact",
                 check="T6 Key personnel", title=f"{kr['role']}: " + ("not named" if not p else f"{p.years} years" + ("" if ok else f", below the {kr['years']} required")),
                 detail=(f"{p.name}, {p.years} years against {kr['years']} required." if p else
                         f"Form C names no {kr['role']}; {kr['years']} years required."),
                 evidence=ev(d, p.page, p.quote) if p else [], proposed_points=1.25 if ok else 0.0,
                 severity="info" if ok else "attention",
                 clarify=None if ok else f"Please name your proposed {kr['role']} and state their years of relevant experience.")
    return coverage


# --- Commercial -----------------------------------------------------------------------------------------------------

def check_commercial(rfp: RfpFacts, s: SubmissionFacts, doc: Document, sink: _Sink, fw: Framework) -> dict:
    d = doc.doc_id
    lots = {}
    for lot in ("A", "B"):
        rows = s.schedules.get(lot, [])
        stated = sum(r.amount for r in rows)
        corrected = sum(round(r.quantity * r.unit_price, 2) for r in rows)
        for r in rows:
            exp = round(r.quantity * r.unit_price, 2)
            if abs(exp - r.amount) > 0.01:
                sink.add("commercial", kind="arithmetic", basis="Fact",
                         check="Arithmetic", title=f"Lot {lot}, item {r.item}: {'under' if r.amount < exp else 'over'}-extended by {_usd(abs(r.amount - exp))}",
                         detail=f"{r.quantity:,.0f} {r.unit} × {_usd(r.unit_price)} = {_usd(exp)}; the schedule states {_usd(r.amount)}.",
                         evidence=ev(d, r.page, r.quote), severity="critical")
        total = s.lot_totals.get(lot)
        stated_total = float(total.text.replace("$", "").replace(",", "")) if total else stated
        if total and abs(stated_total - stated) > 0.01:
            sink.add("commercial", kind="arithmetic", basis="Fact", check="Arithmetic", title=f"Lot {lot}: total does not equal the sum of items",
                     detail=f"Items sum to {_usd(stated)}; the stated total is {_usd(stated_total)}.",
                     evidence=ev(d, total.page, total.quote), severity="critical")
        ps = next((r.amount for r in rows if r.unit == "PS"), 0.0)
        lots[lot] = {"stated": stated_total, "corrected": round(corrected, 2), "provisional": ps,
                     "normalisation": round(rfp.provisional.get(lot, ps) - ps, 2)}
    disc = (s.discount_pct or 0.0) / 100
    sum_stated = sum(v["stated"] for v in lots.values())
    combined_stated = s.combined or 0.0
    expected_combined = round(sum_stated * (1 - disc), 2)
    if s.combined is not None and abs(expected_combined - combined_stated) > 1:
        sink.add("commercial", kind="arithmetic", basis="Fact", check="Arithmetic", title="Combined offer does not equal the lots less the discount",
                 detail=f"{_usd(sum_stated)} less {disc:.1%} is {_usd(expected_combined)}; the combined offer states {_usd(combined_stated)}.",
                 evidence=ev(d, s.combined_cited.page, s.combined_cited.quote), severity="critical")
    combined_corrected = round(sum(v["corrected"] for v in lots.values()) * (1 - disc), 2)
    applied = apply_correction_rule(combined_stated, combined_corrected, fw.correction_rule)  # type: ignore[arg-type]
    normalisation = round(sum(v["normalisation"] for v in lots.values()), 2)
    evaluated = round(applied + normalisation, 2)
    notes = [f"Combined offer as stated: {_usd(combined_stated)}.",
             f"Arithmetically corrected: {_usd(combined_corrected)}."]
    if abs(combined_corrected - combined_stated) > 0.01:
        notes.append("Under clause 2.6 the lower figure applies: " + (
            f"the stated offer stands and the tenderer carries the {_usd(combined_corrected - combined_stated)} error."
            if combined_stated < combined_corrected else f"the tender is evaluated at the corrected {_usd(combined_corrected)}."))
    if normalisation:
        notes.append(f"Provisional sums restored to the Employer's amounts: {_usd(normalisation)} added.")
    notes.append(f"Evaluated price: {_usd(evaluated)}.")
    sink.add("commercial", criterion="P1", kind="price", basis="Fact", check="Evaluated price", title=f"Evaluated price {_usd(evaluated)}",
             detail=" ".join(notes), value=evaluated,
             evidence=ev(d, s.combined_cited.page, s.combined_cited.quote) if s.combined_cited else [],
             severity="attention" if (normalisation or abs(combined_corrected - combined_stated) > 0.01) else "info")
    if s.cashflow:
        cf_total = sum(s.cashflow)
        share = front_loading(s.cashflow, fw.thresholds["front_loading_share"])
        months = round(len(s.cashflow) * fw.thresholds["front_loading_share"])
        heavy = share > fw.thresholds["front_loading_max"]
        sink.add("commercial", kind="cashflow", basis="Fact" if not heavy else "Interpretation",
                 check="Cash flow profile", title=f"Cash flow: {share:.0%} of value in the first {months} months" + (" (front-loaded)" if heavy else ""),
                 detail=(f"The forecast totals {_usd(cf_total)} over {len(s.cashflow)} months. "
                         + (f"More than {fw.thresholds['front_loading_max']:.0%} in the first {months} months suggests front-loaded "
                            "pricing, which shifts risk to the Employer if the contractor fails later." if heavy
                            else "The profile is not front-loaded.")),
                 evidence=ev(d, s.cashflow_cited.page, s.cashflow_cited.quote), severity="attention" if heavy else "info",
                 clarify=("Please explain the basis of your cash flow forecast, which places "
                          f"{share:.0%} of the value in the first {months} months." if heavy else None))
    est = fw.pre_tender_estimate
    if est:
        ratio = evaluated / est
        low = ratio < fw.thresholds["abnormally_low"]
        sink.add("commercial", kind="threshold", basis="Fact",
                 check="Pre-tender estimate", title=f"Evaluated price is {abs(1 - ratio):.1%} {'below' if ratio < 1 else 'above'} the pre-tender estimate",
                 detail=f"Pre-tender estimate {_usd(est)}." + (" Below the abnormally-low threshold of "
                        f"{fw.thresholds['abnormally_low']:.0%}: seek an explanation of the price." if low else ""),
                 severity="critical" if low else "info", method="comparison with the client's estimate")
    return {"lots": lots, "sum_stated": sum_stated, "discount_pct": s.discount_pct or 0.0, "combined_stated": combined_stated,
            "combined_corrected": combined_corrected, "normalisation": normalisation, "evaluated": evaluated,
            "cashflow": s.cashflow}


# --- Contract -------------------------------------------------------------------------------------------------------

_PCT = re.compile(r"(\d+(?:\.\d+)?)%")


def check_contract(rfp: RfpFacts, s: SubmissionFacts, doc: Document, sink: _Sink, fw: Framework, evaluated: float) -> None:
    d = doc.doc_id
    if not s.deviations:
        sink.add("contract", criterion="K1", kind="deviation", basis="Fact", check="Contract deviations", title="No deviations declared in Form G",
                 detail="The tenderer accepts the contract particulars as issued.", proposed_points=0.0)
    for dv in s.deviations:
        rh = fw.risk_heads.get(dv.particular, {"head": "Unclassified", "material": True})
        material = rh["material"]
        quant = ""
        a, b = _PCT.findall(dv.requirement), _PCT.findall(dv.proposed)
        if len(a) == 1 and len(b) == 1 and a != b:
            fa, fb = float(a[0]), float(b[0])
            quant = (f" At the evaluated price of {_usd(evaluated)}, {fa:g}% is {_usd(evaluated * fa / 100)} and {fb:g}% is "
                     f"{_usd(evaluated * fb / 100)}: {'a reduction' if fb < fa else 'an increase'} of {_usd(abs(evaluated * (fb - fa) / 100))}.")
        else:
            ma, mb = re.findall(r"\$([\d,]+)", dv.requirement), re.findall(r"\$([\d,]+)", dv.proposed)
            if len(ma) == 1 and len(mb) == 1 and ma != mb:
                quant = f" The figure changes from ${ma[0]} to ${mb[0]}."
        sink.add("contract", criterion="K1", kind="deviation", basis="Fact",
                 method="risk-head table (prototype stand-in for a model classification)",
                 check="Contract deviations", title=f"{dv.particular}: {dv.proposed}",
                 detail=f"Contract particular: {dv.requirement}. Risk head: {rh['head']}; "
                        f"{'material' if material else 'minor'} under the signed-off framework.{quant} "
                        f"Reason given: {dv.reason}. Whether to accept it is for the client's advisers.",
                 evidence=ev(d, dv.page, dv.quote),
                 proposed_points=-fw.deduction["material" if material else "minor"],
                 severity="critical" if material else "attention",
                 clarify=f"Please confirm whether you will withdraw your proposed change to {dv.particular.lower()}.")


# --- Integrity ------------------------------------------------------------------------------------------------------

def check_integrity_single(s: SubmissionFacts, doc: Document, sink: _Sink, fw: Framework) -> None:
    d = doc.doc_id
    if s.litigation:
        amounts = [float(x.replace(",", "")) for x in re.findall(r"\$([\d,]+)", s.litigation.text)]
        over = [x for x in amounts if x > fw.thresholds["litigation_value"]]
        sink.add("integrity", kind="disclosure", basis="Fact",
                 check="Litigation", title="Litigation disclosed over the threshold" if over else "No litigation over the threshold disclosed",
                 detail=(f"Form O discloses a matter of {_usd(over[0])}, above the {_usd(fw.thresholds['litigation_value'])} "
                         "threshold. Consider its effect on capacity and financial standing." if over
                         else "Form O discloses no matter above the threshold."),
                 evidence=ev(d, s.litigation.page, s.litigation.quote), severity="attention" if over else "info",
                 clarify=("Please give the current status and expected outcome of the matter disclosed in Form O." if over else None))
    if s.terminations:
        terminated = not s.terminations.text.startswith("No contract")
        sink.add("integrity", kind="disclosure", basis="Fact",
                 check="Terminations", title="Contract terminations disclosed" if terminated else "No terminations in the last five years",
                 detail=s.terminations.text, evidence=ev(d, s.terminations.page, s.terminations.quote),
                 severity="attention" if terminated else "info")


def check_integrity_cross(subs: list[tuple[SubmissionFacts, Document, _Sink]], fw: Framework) -> list[dict]:
    rates = {s.tenderer: {f"Lot {lot} item {r.item}": r.unit_price for lot, rows in s.schedules.items() for r in rows if r.unit != "PS"}
             for s, _, _ in subs}
    by_name = {s.tenderer: (s, doc, sink) for s, doc, sink in subs}
    pairs = []
    for a, b, same in identical_values(rates, int(fw.thresholds["identical_rates_min"])):
        pairs.append({"a": a, "b": b, "items": same})
        for me, other in ((a, b), (b, a)):
            s, doc, sink = by_name[me]
            rows = {f"Lot {lot} item {r.item}": r for lot, rs in s.schedules.items() for r in rs}
            sink.add("integrity", kind="cross", basis="Fact", method="cross-tender comparison (deterministic)",
                     check="Identical rates", title=f"Identical unit rates with {other.replace(' (fictional)', '')} on {len(same)} items",
                     detail=f"Identical rates on: {', '.join(same)}. Identical rates across independent tenders can indicate "
                            "collusion; they can also have innocent causes, such as a shared subcontract quotation. This is an "
                            "indicator for the procurement integrity process, not a finding of collusion.",
                     evidence=[e for k in same[:3] for e in ev(doc.doc_id, rows[k].page, rows[k].quote)], severity="critical")
    subs_by = {s.tenderer: {c.text: c for c in s.subcontractors} for s, _, _ in subs}
    names = sorted(subs_by)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            for shared in sorted(set(subs_by[a]) & set(subs_by[b])):
                for me, other in ((a, b), (b, a)):
                    s, doc, sink = by_name[me]
                    c = subs_by[me][shared]
                    sink.add("integrity", kind="cross", basis="Fact", method="cross-tender comparison (deterministic)",
                             check="Shared subcontractors", title=f"Shares a subcontractor with {other.replace(' (fictional)', '')}",
                             detail=f"Both tenders name {shared}. Common in a small market; read together with any other indicator.",
                             evidence=ev(doc.doc_id, c.page, c.quote), severity="attention")
    return pairs


# --- The whole evaluation -------------------------------------------------------------------------------------------

def evaluate_all(rfp: RfpFacts, rfp_doc: Document, subs: list[tuple[SubmissionFacts, Document]],
                 receipts: dict[str, str], fw: Framework) -> dict:
    findings: list[Finding] = []
    sinks, commercial, coverage = [], {}, {}
    for s, doc in subs:
        key = doc.doc_id.removeprefix("tender_")
        sink = _Sink(key, s.tenderer, {doc.doc_id: doc}, s.method, findings)
        sinks.append((s, doc, sink))
        check_receipt(s, sink, receipts.get(key), receipts["deadline"])
        check_gate(rfp, s, doc, sink, fw)
        coverage[s.tenderer] = check_technical(rfp, s, doc, sink, fw)
        commercial[s.tenderer] = check_commercial(rfp, s, doc, sink, fw)
        check_contract(rfp, s, doc, sink, fw, commercial[s.tenderer]["evaluated"])
        check_integrity_single(s, doc, sink, fw)
    pairs = check_integrity_cross(sinks, fw)

    # Cross-tender rate comparison: each priced item against the median of all tenderers.
    rate_table = {}
    for s, doc, sink in sinks:
        for lot, rows in s.schedules.items():
            for r in rows:
                if r.unit != "PS":
                    rate_table.setdefault(f"Lot {lot} item {r.item}", {})[s.tenderer] = (r.unit_price, r, doc)
    outliers = {}
    for item, row in rate_table.items():
        devs = deviations_from_median({k: v[0] for k, v in row.items()})
        outliers[item] = {k: round(v, 3) for k, v in devs.items()}
        for name, dev in devs.items():
            if abs(dev) > fw.thresholds["rate_outlier"]:
                _, r, doc = row[name]
                sink = next(x[2] for x in sinks if x[0].tenderer == name)
                sink.add("commercial", kind="outlier", basis="Fact", method="cross-tender comparison (deterministic)",
                         check="Rate outliers", title=f"{item} ({r.description}): rate {abs(dev):.0%} {'above' if dev > 0 else 'below'} the median",
                         detail=f"Rate {_usd(r.unit_price)} against a median of {_usd(sorted(v[0] for v in row.values())[len(row) // 2])} "
                                f"across {len(row)} tenders. An unbalanced rate can signal front-loading or a misunderstanding of "
                                "the scope; it matters most where quantities may change.",
                         evidence=ev(doc.doc_id, r.page, r.quote), severity="attention",
                         clarify=f"Please explain the build-up of your rate for {item} ({r.description}).")

    lot_prices = {n: {lot: v["stated"] + v["normalisation"] for lot, v in c["lots"].items()} for n, c in commercial.items()}
    award = cheapest_award(lot_prices, {n: c["evaluated"] for n, c in commercial.items()})
    return {"findings": findings, "commercial": commercial, "coverage": coverage, "outliers": outliers,
            "identical": pairs, "award": award, "lot_prices": lot_prices}
