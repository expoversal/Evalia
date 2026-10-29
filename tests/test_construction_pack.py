"""End-to-end checks of the construction pack on the fictional tender."""
import json
from pathlib import Path

import pytest

from evalia.engine.documents import load_pdf
from evalia.engine.findings import Decision
from evalia.engine.llm import Gateway, Profile, ResidencyPolicy
from evalia.engine.report import build_markdown, scores
from packs.construction.evaluate import evaluate_bid, load_default_criteria
from packs.construction.extract import ModelReading, extract_with_model, read_forms

FIX = Path(__file__).parent / "fixtures" / "synthetic"
CRIT = load_default_criteria()


def run(key):
    doc = load_pdf(FIX / f"bid_{key}.pdf")
    return doc, evaluate_bid(read_forms(doc, CRIT.compliance_items), doc, CRIT)


def titles(fs, kind):
    return [f.title for f in fs if f.kind == kind]


def test_every_evidence_quote_verifies():
    for key in ("northfield", "cobalt", "harborpine"):
        _, fs = run(key)
        assert all(f.fully_verified for f in fs), key


def test_northfield_clean():
    _, fs = run("northfield")
    assert sum(f.proposed_points or 0 for f in fs if f.criterion == "C1") == 10.0
    assert not [f for f in fs if f.severity == "critical"]


def test_cobalt_bond_and_arithmetic():
    _, fs = run("cobalt")
    assert any("Bid bond" in t and "not found" in t for t in titles(fs, "compliance"))
    arith = [f for f in fs if f.kind == "arithmetic"]
    assert any("item 2" in f.title and "$18,000.00" in f.title for f in arith)
    excluded = [f.detail for f in fs if f.kind == "record" and f.proposed_points == 0]
    assert any("9,200,000 is below the minimum" in d for d in excluded)
    assert any("2016 is outside" in d for d in excluded)


def test_harborpine_unsubstantiated_rating_and_subcontract():
    _, fs = run("harborpine")
    sub = [f for f in fs if f.kind == "substantiation"]
    assert len(sub) == 1 and "Ironwood" in sub[0].title and "'Marginal'" in sub[0].detail
    assert sub[0].severity == "critical" and len(sub[0].evidence) == 2
    excluded = " ".join(f.detail for f in fs if f.kind == "record" and f.proposed_points == 0)
    assert "Subcontractor" in excluded and "office building" in excluded
    assert sum(f.proposed_points or 0 for f in fs if f.criterion == "C1") == 5.0


def test_full_run_report(tmp_path):
    allf, docs = [], []
    for key in ("northfield", "cobalt", "harborpine"):
        d, fs = run(key)
        docs.append(d)
        allf += fs
    ds = {f.id: Decision(finding_id=f.id, action="accept", evaluator="E. Valuator (fictional)") for f in allf}
    caps = {"C1": ("Relevant completed projects", 12.5), "C2": ("Safety", 5.0)}
    table = scores(allf, ds, caps)
    assert table["Northfield Builders Inc. (fictional)"] == {"C1": 10.0, "C2": 5.0}
    assert table["Cobalt Ridge Construction LLC (fictional)"] == {"C1": 7.5, "C2": 3.0}
    assert table["Harbor & Pine Contractors (fictional)"] == {"C1": 5.0, "C2": 0.0}
    md = build_markdown(context={"title": "t", "reference": "r", "owner": "o"}, signoff={"by": "x", "at": "now"},
                        findings=allf, decisions=ds, caps=caps, not_assessed=CRIT.not_assessed,
                        inputs=[{"doc_id": d.doc_id, "sha256": d.sha256} for d in docs], model_calls=[], methods={"form reader"})
    assert "NOT VERIFIED" not in md and "Report SHA-256" in md


class FakeGateway(Gateway):
    """Stands in for a model: returns a fixed reading, including one invented quote."""

    def __init__(self, tmp, reading):
        super().__init__(Profile(name="fake", provider="anthropic", model="fake", residency="self_hosted",
                                 region="local", api_key_env="UNUSED"), ResidencyPolicy(allowed=["self_hosted"]), tmp)
        self.reading = reading

    def structured(self, task, prompt, schema):
        assert "=== Page 3 ===" in prompt and "{{" not in prompt
        return schema.model_validate(self.reading)


def test_model_output_is_checked(tmp_path):
    doc = load_pdf(FIX / "bid_harborpine.pdf")
    reading = {
        "projects": [
            {"name": "Clearwater Logistics Warehouse", "building_type": "warehouse", "owner": "Clearwater Logistics",
             "completed": 2021, "contract_value": 13900000, "role": "Prime contractor", "claimed_rating": "Very Good", "page": 3,
             "quote": "1 Clearwater Logistics Warehouse warehouse Clearwater Logistics 2021 $13,900,000.00 Prime contractor Very Good"},
            # Invented by the "model": wrong value, and a quote that is not on the page.
            {"name": "Silver Lake Assembly Plant", "building_type": "industrial building", "owner": "Silver Lake Motors",
             "completed": 2024, "contract_value": 16600000, "role": "Prime contractor", "claimed_rating": "Satisfactory", "page": 3,
             "quote": "4 Silver Lake Assembly Plant industrial building Silver Lake Motors 2024 $16,600,000.00 Prime contractor Satisfactory"},
        ],
        "ratings": [{"project_name": "Clearwater Logistics Warehouse", "rating": "Very Good", "page": 4,
                     "quote": "Overall performance rating: Very Good"}],
        "emr": 1.12, "emr_page": 4,
        "emr_quote": "Experience Modification Rate of Harbor & Pine Contractors (fictional) is 1.12",
    }
    facts = extract_with_model(doc, FakeGateway(tmp_path, reading), CRIT.compliance_items)
    fs = evaluate_bid(facts, doc, CRIT)
    silver = [f for f in fs if f.kind == "record" and "Silver Lake" in f.title][0]
    assert not silver.fully_verified and silver.basis == "Interpretation" and silver.severity == "critical"
    clear = [f for f in fs if f.kind == "record" and "Clearwater" in f.title][0]
    # The rating quote was cited on the wrong page (it is on page 5), so it fails verification.
    assert not clear.fully_verified
