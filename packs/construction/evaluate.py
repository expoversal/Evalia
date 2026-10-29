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
from evalia.engine.numbers import words_to_number
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
    due_diligence: list[str] = []


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
    if rfp.security_pct is not None:
        need = round((s.combined or 0) * rfp.security_pct / 100, 2)
        if s.security_amount is None:
            sink.add("gate", check="Tender security", kind="presence", basis="Fact", title="Tender security not found",
                     detail=f"A tender security of {rfp.security_pct:g}% of the Combined Offer is required.", severity="critical")
        else:
            short_amt, short_days = s.security_amount < need, s.security_days < (rfp.security_days or 0)
            problems = ([f"amount {_usd(s.security_amount)} is below {_usd(need)}"] if short_amt else []) + (
                [f"valid for {s.security_days} days, not the {rfp.security_days} required"] if short_days else [])
            sink.add("gate", check="Tender security", kind="threshold", basis="Fact",
                     title="Tender security: " + ("; ".join(problems) if problems else f"{_usd(s.security_amount)}, {s.security_days} days"),
                     detail=f"Required: at least {rfp.security_pct:g}% of the Combined Offer ({_usd(need)}), valid for "
                            f"{rfp.security_days} days." + (" A security that does not cover the tender's validity cannot be "
                            "called on later in the evaluation." if short_days else ""),
                     evidence=ev(d, s.forms["Tender Security"].page, s.forms["Tender Security"].quote) + ev(d, s.security.page, s.security.quote),
                     severity="critical" if problems else "info",
                     clarify=(f"Please provide a tender security valid for {rfp.security_days} days." if short_days else None))
    if rfp.addenda:
        got = set(s.addenda.text.split()) if s.addenda else set()
        missing = [a for a in rfp.addenda if a not in got]
        sink.add("gate", check="Addenda acknowledged", kind="set", basis="Fact",
                 title="All addenda acknowledged" if not missing else f"Addendum No. {', '.join(missing)} not acknowledged",
                 detail=f"Addenda issued: {', '.join(rfp.addenda)}." + ("" if not missing else " A tender that does not acknowledge an "
                        "addendum may not have priced it."),
                 evidence=ev(d, s.addenda.page, s.addenda.quote) if s.addenda else [], severity="critical" if missing else "info",
                 clarify=(f"Please confirm that your tender includes Addendum No. {', '.join(missing)} at no change to the price."
                          if missing else None))
    tech_pages = [pg for pg in doc.pages if pg.number in s.volume_pages.get("Volume 2", [])
                  and "Form K - Relevant Experience" not in pg.text and "Owner Performance Evaluation" not in pg.text]
    leaks = [(pg.number, m.group(0)) for pg in tech_pages for m in re.finditer(r"[^.]*\$[\d,]+(?:\.\d\d)?[^.]*\.", normalise(pg.text))]
    sink.add("gate", check="No prices in technical tender", kind="presence", basis="Fact",
             title="Price found in the technical tender" if leaks else "No prices in the technical tender",
             detail=("The request for proposal requires Volume 2 to contain no prices, so that technical evaluators are not "
                     "influenced by price. Evaluators should be told to disregard it." if leaks
                     else "No currency amounts in Volume 2, apart from contract values of past projects."),
             evidence=[e for pn, q in leaks[:2] for e in ev(d, pn, q.strip())], severity="attention" if leaks else "info",
             method="currency scan (deterministic)")
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
    in_words = words_to_number(s.words.text) if s.words else None
    if s.words and in_words is not None and abs(in_words - combined_stated) > 0.5:
        sink.add("commercial", check="Words and figures", kind="arithmetic", basis="Fact",
                 title=f"Words state {_usd(in_words)}; figures state {_usd(combined_stated)}",
                 detail=("Under the request for proposal the amount in words prevails, so the Combined Offer is taken as "
                         f"{_usd(in_words)}, a difference of {_usd(in_words - combined_stated)}." if rfp.words_prevail else
                         "The request for proposal states no rule; the panel must decide which governs."),
                 evidence=ev(d, s.words.page, s.words.quote) + (ev(d, s.offer.page, s.offer.quote) if s.offer else []),
                 severity="critical",
                 clarify=f"Your Combined Offer in words ({s.words.text}) differs from the figures ({_usd(combined_stated)}). "
                         "Please confirm that you accept the amount in words.")
        if rfp.words_prevail:
            combined_stated = in_words
    elif s.words:
        sink.add("commercial", check="Words and figures", kind="arithmetic", basis="Fact", title="Words agree with figures",
                 detail=f"The Combined Offer in words matches {_usd(combined_stated)}.", evidence=ev(d, s.words.page, s.words.quote))
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
    comparison = evaluated
    outside = bool(rfp.home_state and s.home_state and rfp.home_state not in s.home_state.text)
    if outside and rfp.preference_pct:
        comparison = round(evaluated * (1 + rfp.preference_pct / 100), 2)
        notes.append(f"Registered outside the {rfp.home_state}: {rfp.preference_pct:g}% added for comparison only, giving "
                     f"{_usd(comparison)}. The contract price is unaffected.")
    sink.add("commercial", criterion="P1", kind="price", basis="Fact", check="Evaluated price",
             title=f"Evaluated price {_usd(evaluated)}" + (f"; {_usd(comparison)} for comparison" if comparison != evaluated else ""),
             detail=" ".join(notes), value=comparison,
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
            "words": in_words, "comparison": comparison, "preference": outside and bool(rfp.preference_pct),
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

def check_qualification(rfp: RfpFacts, s: SubmissionFacts, doc: Document, sink: _Sink, deadline: str) -> None:
    d, due = doc.doc_id, datetime.fromisoformat(deadline)
    for label, rec in (("General Building Contractor licence", s.licence), ("Tax clearance certificate", s.tax_certificate)):
        if not rec:
            sink.add("integrity", check=label, kind="presence", basis="Fact", title=f"{label} not found",
                     detail="Form B does not give it.", severity="critical")
            continue
        expiry = datetime.strptime(rec["expiry"], "%d %B %Y")
        problems = []
        if expiry < due:
            problems.append(f"expired on {rec['expiry']}, before the submission date")
        if rec.get("class") and rfp.licence_class and rec["class"] != rfp.licence_class:
            problems.append(f"{rec['class']}, not the {rfp.licence_class} required")
        sink.add("integrity", check=label, kind="threshold", basis="Fact",
                 title=f"{label}: " + ("; ".join(problems) if problems else f"valid until {rec['expiry']}"),
                 detail=("It must be valid on the submission date." + (" An expired certificate makes the tenderer ineligible "
                         "unless the panel accepts a renewal as a clarification." if problems else "")),
                 evidence=ev(d, rec["page"], rec["quote"]), severity="critical" if problems else "info",
                 clarify=(f"Please provide your current {label.lower()}, valid on the submission date." if problems else None))
    if rfp.turnover_multiple and s.turnover:
        values = [float(c.text.replace("$", "").replace(",", "")) for c in s.turnover]
        avg, need = sum(values) / len(values), rfp.turnover_multiple * (s.combined or 0)
        low = avg < need
        sink.add("integrity", check="Financial standing", kind="threshold", basis="Fact",
                 title=f"Average turnover {_usd(avg)}" + (f", below the {_usd(need)} required" if low else ""),
                 detail=f"Average over {len(values)} years against {rfp.turnover_multiple:g} times the Combined Offer ({_usd(need)}). "
                        + ("A tenderer below the threshold may lack the capacity to carry a contract of this size." if low else ""),
                 evidence=[e for c in s.turnover for e in ev(d, c.page, c.quote)], severity="critical" if low else "info")


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


# --- Further checks drawn from the reference tenders (docs/06-check-catalogue.md) -------------------------------------

def _date(text: str) -> datetime | None:
    try:
        return datetime.strptime(text.strip(), "%d %B %Y")
    except ValueError:
        return None


def check_opening(rfp: RfpFacts, s: SubmissionFacts, sink: _Sink, opening: dict, count: int) -> None:
    if rfp.one_tender:
        sink.add("receipt", check="One tender per tenderer", kind="set", basis="Fact", method="opening record",
                 title="One tender received" if count == 1 else f"{count} tenders received from this tenderer",
                 detail=("Only one tender per tenderer is considered." + ("" if count == 1 else
                         " Under the request for proposal, none of them can be considered.")),
                 severity="info" if count == 1 else "critical")
    if rfp.authority_at_opening:
        ok = bool(opening.get("letter_of_authority"))
        sink.add("receipt", check="Letter of authority at opening", kind="presence", basis="Fact", method="opening record",
                 title="Representative's letter of authority in order" if ok else "No letter of authority at opening",
                 detail="Recorded by the opening panel.", severity="info" if ok else "attention")


def check_gate_more(rfp: RfpFacts, s: SubmissionFacts, doc: Document, sink: _Sink, deadline: str) -> None:
    d, due = doc.doc_id, datetime.fromisoformat(deadline)
    site = s.forms.get("Site Visit Certificate")
    sink.add("gate", check="Site visit", kind="presence", basis="Fact",
             title="Site Visit Certificate present" if site else "Site Visit Certificate missing",
             detail="Attendance at the site visit is mandatory." + ("" if site else " Without the certificate, the panel cannot "
                    "confirm that the tenderer saw the site; check the attendance register before deciding."),
             evidence=ev(d, site.page, site.quote) if site else [], severity="info" if site else "critical",
             clarify=None if site else "Please provide your Site Visit Certificate, or state the date your representative attended.")
    for form, limit in rfp.page_limits.items():
        n = s.form_pages.get(form)
        if n is not None:
            m = s.forms[form]
            sink.add("gate", check="Page limits", kind="threshold", basis="Fact",
                     title=f"{form.split(' - ')[0]}: {n} page{'s' if n > 1 else ''} of {limit} allowed",
                     detail="Within the limit." if n <= limit else f"Pages beyond {limit} should not be read by the evaluators.",
                     evidence=ev(d, m.page, m.quote), severity="info" if n <= limit else "attention")
    if rfp.alternatives_with_base:
        sink.add("gate", check="Alternatives", kind="presence", basis="Fact",
                 title="Alternative tender offered" if s.alternative else "No alternative tender",
                 detail=("It is considered only if the base tender is compliant, and is evaluated separately." if s.alternative
                         else "Only the base tender is evaluated."),
                 evidence=ev(d, s.alternative.page, s.alternative.quote) if s.alternative else [])
    if rfp.subcontractor_tax and s.subcontractors:
        bad = [c for c in s.subcontractors if not c.tax or (_date(c.tax) or due) < due]
        sink.add("gate", check="Documents for each entity", kind="set", basis="Fact",
                 title=(f"Tax clearance for all {len(s.subcontractors)} subcontractors" if not bad else
                        "Tax clearance missing or expired: " + ", ".join(c.text.replace(" (fictional)", "") for c in bad)),
                 detail="Each named subcontractor must provide its own tax clearance certificate, valid on the submission date.",
                 evidence=[e for c in (bad or s.subcontractors)[:2] for e in ev(d, c.page, c.quote)],
                 severity="critical" if bad else "info",
                 clarify=("Please provide a current tax clearance certificate for: "
                          + ", ".join(c.text for c in bad) + ".") if bad else None)
    if rfp.sales_tax_separate:
        foreign = s.currencies
        issues = ([f"amounts in another currency ({', '.join(c.text for c in foreign[:2])})"] if foreign else []) + (
            [] if s.sales_tax else ["sales tax not stated separately"])
        sink.add("gate", check="Currency and tax", kind="presence", basis="Fact",
                 title="US dollars; sales tax stated separately" if not issues else "Currency and tax: " + "; ".join(issues),
                 detail="Prices must be in US dollars, excluding sales tax, with the tax stated separately on the Combined Offer."
                        + ("" if s.sales_tax else " Without it, the panel cannot confirm that the price excludes tax."),
                 evidence=ev(d, s.sales_tax.page, s.sales_tax.quote) if s.sales_tax else [],
                 severity="info" if not issues else "attention",
                 clarify=None if s.sales_tax else "Please confirm that your Combined Offer excludes sales tax, and state the tax separately.")


def check_technical_more(rfp: RfpFacts, s: SubmissionFacts, doc: Document, sink: _Sink) -> None:
    d = doc.doc_id
    if rfp.plant:
        have = {p["item"]: p for p in s.plant}
        short = [f"{r['item']} ({have[r['item']]['qty'] if r['item'] in have else 0} of {r['qty']})"
                 for r in rfp.plant if have.get(r["item"], {}).get("qty", 0) < r["qty"]]
        sink.add("technical", check="Plant", kind="set", basis="Fact",
                 title="Minimum plant offered" if not short else "Plant short: " + "; ".join(short),
                 detail="Against the minimum plant in the request for proposal. Leased plant counts if it is committed for the works.",
                 evidence=[e for p in s.plant[:3] for e in ev(d, p["page"], p["quote"])], severity="info" if not short else "attention",
                 clarify=None if not short else "Please confirm how you will provide the minimum plant: " + "; ".join(short) + ".")
    for req in rfp.performance:
        got = s.technical_data.get(req["parameter"])
        if not got:
            sink.add("technical", check="Specification values", kind="presence", basis="Fact", title=f"{req['parameter']}: not offered",
                     detail="Form T gives no value.", severity="attention")
            continue
        val = float(got.text)
        ok = val >= req["value"] if req["limit"] == "minimum" else val <= req["value"]
        sink.add("technical", check="Specification values", kind="threshold", basis="Fact",
                 title=f"{req['parameter']}: {got.text} offered" + ("" if ok else f", {req['limit']} {req['value']:g}"),
                 detail=f"The requirement is a {req['limit']} of {req['value']:g}." + ("" if ok else " The offer does not meet it."),
                 evidence=ev(d, got.page, got.quote), severity="info" if ok else "critical",
                 clarify=None if ok else f"Your offered value for {req['parameter'].lower()} ({got.text}) does not meet the "
                                         f"{req['limit']} of {req['value']:g}. Please confirm your offer.")
    if rfp.resident_pct is not None and s.resident:
        ok = s.resident_pct >= rfp.resident_pct
        sink.add("technical", check="Local workforce", kind="threshold", basis="Fact",
                 title=f"Local workforce {s.resident_pct:g}%" + ("" if ok else f", below the {rfp.resident_pct:g}% required"),
                 detail=f"At least {rfp.resident_pct:g}% of the site workforce must be resident in the State.",
                 evidence=ev(d, s.resident.page, s.resident.quote), severity="info" if ok else "critical")


def check_commercial_more(s: SubmissionFacts, doc: Document, sink: _Sink) -> None:
    d = doc.doc_id
    diffs = []
    for lot in ("A", "B"):
        sched = s.lot_totals.get(lot)
        if sched and lot in s.letter_prices:
            val = float(sched.text.replace("$", "").replace(",", ""))
            if abs(val - s.letter_prices[lot]) > 0.5:
                diffs.append(f"Lot {lot}: letter {_usd(s.letter_prices[lot])}, schedule {_usd(val)}")
    if s.combined is not None and "combined" in s.letter_prices and abs(s.combined - s.letter_prices["combined"]) > 0.5:
        diffs.append(f"Combined: letter {_usd(s.letter_prices['combined'])}, offer page {_usd(s.combined)}")
    sink.add("commercial", check="Letter against schedules", kind="arithmetic", basis="Fact",
             title="Letter of Tender agrees with the schedules" if not diffs else "Letter of Tender differs from the schedules",
             detail="Prices in the Letter of Tender against the priced schedules." + ("" if not diffs else " " + "; ".join(diffs) + "."),
             evidence=ev(d, s.offer.page, s.offer.quote) if s.offer else [], severity="info" if not diffs else "critical")
    blank = [f"Lot {lot} item {r.item}" for lot, rows in s.schedules.items() for r in rows if r.unit_price == 0 or r.amount == 0]
    sink.add("commercial", check="Unpriced items", kind="set", basis="Fact",
             title="Every item priced" if not blank else f"{len(blank)} items unpriced",
             detail=("No blank or zero rates." if not blank else "Unpriced: " + ", ".join(blank)
                     + ". Unless the tender says otherwise, they are deemed included in other rates."),
             severity="info" if not blank else "attention")


def check_qualification_more(rfp: RfpFacts, s: SubmissionFacts, doc: Document, sink: _Sink) -> None:
    d = doc.doc_id
    if rfp.accounts_years and s.accounts:
        given = re.findall(r"\d{4}", s.accounts.text)
        missing = [y for y in rfp.accounts_years if y not in given]
        sink.add("integrity", check="Accounts", kind="set", basis="Fact",
                 title=f"Audited accounts {', '.join(given)}" + ("" if not missing else f"; {', '.join(missing)} missing"),
                 detail=f"Required: {', '.join(rfp.accounts_years)}." + ("" if not missing else " The latest year is missing, so the "
                        "financial standing rests on older figures."),
                 evidence=ev(d, s.accounts.page, s.accounts.quote), severity="info" if not missing else "attention",
                 clarify=None if not missing else f"Please provide audited accounts for {', '.join(missing)}.")
    if rfp.owner_threshold is not None:
        sink.add("integrity", check="Ownership", kind="presence", basis="Fact",
                 title=f"{len(s.owners)} owners of {rfp.owner_threshold:g}% or more named" if s.owners else "Owners not named",
                 detail="; ".join(f"{o['name']}, {o['pct']:g}%" for o in s.owners) or "Form B names no owners.",
                 evidence=ev(d, s.owners_cited.page, s.owners_cited.quote) if s.owners_cited else [],
                 severity="info" if s.owners else "critical")
    if s.jv and rfp.jv_member_min is not None:
        bad = [f"{m['name'].replace(' (fictional)', '')} {m['pct']:g}%" for m in s.jv
               if m["pct"] < (rfp.jv_lead_min if m["role"].lower().startswith("lead") else rfp.jv_member_min)]
        sink.add("integrity", check="Joint-venture shares", kind="threshold", basis="Fact",
                 title="Joint-venture shares meet the minimums" if not bad else "Joint-venture share below the minimum: " + ", ".join(bad),
                 detail=f"Each member at least {rfp.jv_member_min:g}%, the lead at least {rfp.jv_lead_min:g}%.",
                 evidence=[e for m in s.jv for e in ev(d, m["page"], m["quote"])], severity="info" if not bad else "critical")


def check_owners_cross(sinks: list[tuple[SubmissionFacts, Document, _Sink]]) -> list[dict]:
    hits = []
    for i, (a, da, sa) in enumerate(sinks):
        for b, db, sb in sinks[i + 1:]:
            shared = sorted({o["name"] for o in a.owners} & {o["name"] for o in b.owners})
            for name in shared:
                hits.append({"a": a.tenderer, "b": b.tenderer, "owner": name})
                for me, other, doc, sink in ((a, b, da, sa), (b, a, db, sb)):
                    pct = next(o["pct"] for o in me.owners if o["name"] == name)
                    sink.add("integrity", check="Shared ownership", kind="cross", basis="Fact",
                             method="cross-tender comparison (deterministic)",
                             title=f"Shares an owner with {other.tenderer.replace(' (fictional)', '')}",
                             detail=f"{name} holds {pct:g}% here and also owns part of the other tenderer. Tenders from commonly "
                                    "owned firms are not independent; read with the anti-collusion certificates and any other "
                                    "indicator, and refer to the procurement integrity process.",
                             evidence=ev(doc.doc_id, me.owners_cited.page, me.owners_cited.quote), severity="critical")
    return hits


# --- The whole evaluation -------------------------------------------------------------------------------------------

def evaluate_all(rfp: RfpFacts, rfp_doc: Document, subs: list[tuple[SubmissionFacts, Document]],
                 receipts: dict[str, str], fw: Framework, opening: dict | None = None) -> dict:
    findings: list[Finding] = []
    sinks, commercial, coverage = [], {}, {}
    for s, doc in subs:
        key = doc.doc_id.removeprefix("tender_")
        sink = _Sink(key, s.tenderer, {doc.doc_id: doc}, s.method, findings)
        sinks.append((s, doc, sink))
        check_receipt(s, sink, receipts.get(key), receipts["deadline"])
        check_opening(rfp, s, sink, (opening or {}).get(key, {}), sum(1 for x, _ in subs if x.tenderer == s.tenderer))
        check_gate(rfp, s, doc, sink, fw)
        check_gate_more(rfp, s, doc, sink, receipts["deadline"])
        coverage[s.tenderer] = check_technical(rfp, s, doc, sink, fw)
        check_technical_more(rfp, s, doc, sink)
        commercial[s.tenderer] = check_commercial(rfp, s, doc, sink, fw)
        check_commercial_more(s, doc, sink)
        check_contract(rfp, s, doc, sink, fw, commercial[s.tenderer]["evaluated"])
        check_qualification(rfp, s, doc, sink, receipts["deadline"])
        check_qualification_more(rfp, s, doc, sink)
        check_integrity_single(s, doc, sink, fw)
    pairs = check_integrity_cross(sinks, fw)
    owners = check_owners_cross(sinks)

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
    return {"findings": findings, "commercial": commercial, "coverage": coverage, "outliers": outliers, "owners": owners,
            "identical": pairs, "award": award, "lot_prices": lot_prices}
