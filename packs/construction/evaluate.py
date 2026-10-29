"""Turn extracted bid facts into findings, using the client's signed-off criteria."""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel

from evalia.engine.documents import Document
from evalia.engine.findings import Evidence, Finding, verify_evidence
from evalia.engine.rules import BandRule, RecordRule
from evalia.engine.verify import normalise

from .extract import BidFacts, values_in_quote

CRITERIA_FILE = Path(__file__).parent / "criteria.yaml"


class Criteria(BaseModel):
    record_rules: list[RecordRule]
    band_rules: list[BandRule]
    compliance_items: list[dict]
    not_assessed: list[str]


def load_default_criteria() -> Criteria:
    return Criteria.model_validate(yaml.safe_load(CRITERIA_FILE.read_text()))


def _key(name: str) -> str:
    return normalise(name).lower()


def evaluate_bid(facts: BidFacts, doc: Document, criteria: Criteria) -> list[Finding]:
    docs = {doc.doc_id: doc}
    out: list[Finding] = []
    n = 0

    def add(**kw) -> None:
        nonlocal n
        n += 1
        out.append(verify_evidence(Finding(id=f"{facts.doc_id}-{n:02d}", subject=facts.bidder, method=facts.method, **kw), docs))

    ratings = {_key(r.project_name): r for r in facts.ratings}

    # Track record: each claimed project is checked against the rule, using the owner's evaluation, not the claim.
    for rule in criteria.record_rules:
        for pr in facts.projects:
            ev = [Evidence(doc_id=doc.doc_id, page=pr.page, quote=pr.quote)]
            mismatches = values_in_quote(pr)
            letter = ratings.get(_key(pr.name))
            if letter:
                ev.append(Evidence(doc_id=doc.doc_id, page=letter.page, quote=letter.quote))
            record = {rule.keyword_field: pr.building_type, rule.year_field: pr.completed,
                      rule.value_field: pr.contract_value, rule.role_field: pr.role,
                      rule.rating_field: letter.rating if letter else None}
            reasons = rule.check(record)
            if mismatches:
                reasons.append("extracted values do not match the quoted text (" + "; ".join(mismatches) + ")")
            qualifies = not reasons
            add(criterion=rule.id, kind="record", basis="Fact",
                title=f"{pr.name}: {'counts' if qualifies else 'does not count'} towards {rule.title.lower()}",
                detail=("Meets every condition of the signed-off rule." if qualifies
                        else "Fails: " + "; ".join(reasons) + "."),
                evidence=ev, proposed_points=rule.points_per_record if qualifies else 0.0,
                severity="info" if qualifies else "attention")

            # Claim against evidence: the check EVA's published example describes.
            if letter is None:
                add(criterion=rule.id, kind="substantiation", basis="Fact",
                    title=f"{pr.name}: no owner performance evaluation supplied",
                    detail=f"The bid claims a rating of '{pr.claimed_rating}' but attaches no owner evaluation for this project "
                           f"(all {facts.pages_checked} pages checked). The claim is unsubstantiated.",
                    evidence=ev, severity="attention")
            elif letter.rating != pr.claimed_rating:
                add(criterion=rule.id, kind="substantiation", basis="Fact",
                    title=f"{pr.name}: claimed rating not substantiated",
                    detail=f"The statement of experience claims '{pr.claimed_rating}'; the owner's own evaluation, attached to the "
                           f"same bid, gives '{letter.rating}'. The owner's rating has been used."
                           + (f" Relying on the claim would have added {rule.points_per_record:g} points."
                              if not rule.check({**record, rule.rating_field: pr.claimed_rating}) and reasons else ""),
                    evidence=ev, severity="critical")

    # Safety: banded score from the certified value.
    for rule in criteria.band_rules:
        if facts.emr is None:
            add(criterion=rule.id, kind="band", basis="Fact", title=f"{rule.title}: not stated",
                detail="No certified value found in the bid; no points proposed.", proposed_points=0.0, severity="attention")
        else:
            pts = rule.points_for(facts.emr)
            add(criterion=rule.id, kind="band", basis="Fact", title=f"{rule.title}: {facts.emr:.2f}",
                detail=f"Certified value {facts.emr:.2f} falls in the band worth {pts:g} of {rule.max_points:g} points.",
                evidence=[Evidence(doc_id=doc.doc_id, page=facts.emr_page or 0, quote=facts.emr_quote or "")],
                proposed_points=pts, severity="info" if pts == rule.max_points else "attention")

    # Compliance items.
    for item in criteria.compliance_items:
        m = facts.markers.get(item["id"])
        if m and m.present:
            add(criterion=item["id"], kind="compliance", basis="Fact", title=f"{item['title']}: present",
                detail="Found in the bid.", evidence=[Evidence(doc_id=doc.doc_id, page=m.page or 0, quote=m.quote or "")])
        else:
            add(criterion=item["id"], kind="compliance", basis="Fact", title=f"{item['title']}: not found",
                detail=f"Searched all {facts.pages_checked} pages; not found. Seek clarification or treat as non-responsive "
                       f"under the tender's rules.", severity="critical")

    # Bid-schedule arithmetic, computed in code.
    total = 0.0
    for row in facts.schedule:
        expected = round(row.quantity * row.unit_price, 2)
        total += row.amount
        if abs(expected - row.amount) > 0.01:
            add(criterion="PRICE", kind="arithmetic", basis="Fact",
                title=f"Bid schedule item {row.item}: extension error of ${row.amount - expected:,.2f}",
                detail=f"{row.quantity:,.0f} {row.unit} x ${row.unit_price:,.2f} = ${expected:,.2f}; the bid states ${row.amount:,.2f}.",
                evidence=[Evidence(doc_id=doc.doc_id, page=row.page, quote=row.quote)], severity="critical")
    if facts.schedule and facts.stated_total is not None and abs(round(total, 2) - facts.stated_total) > 0.01:
        add(criterion="PRICE", kind="arithmetic", basis="Fact", title="Bid schedule total does not equal the sum of items",
            detail=f"Items sum to ${total:,.2f}; the stated total is ${facts.stated_total:,.2f}.",
            evidence=[Evidence(doc_id=doc.doc_id, page=facts.total_page or 0, quote=facts.total_quote or "")], severity="critical")
    elif facts.schedule:
        corrected = sum(round(r.quantity * r.unit_price, 2) for r in facts.schedule)
        if facts.stated_total is not None and abs(corrected - facts.stated_total) > 0.01:
            add(criterion="PRICE", kind="arithmetic", basis="Fact", title="Corrected total differs from the stated bid",
                detail=f"With extensions recomputed, the total is ${corrected:,.2f} against the stated ${facts.stated_total:,.2f} "
                       f"(difference ${facts.stated_total - corrected:,.2f}). Apply the tender's rule for arithmetic errors.",
                evidence=[Evidence(doc_id=doc.doc_id, page=facts.total_page or 0, quote=facts.total_quote or "")], severity="attention")
    return out
