"""Engine tests on synthetic material only."""
from pathlib import Path

import pytest

from evalia.engine.documents import load_pdf
from evalia.engine.findings import Decision, Evidence, Finding, final_points, verify_evidence
from evalia.engine.llm import Gateway, Profile, ResidencyPolicy, ResidencyRefused
from evalia.engine.report import build_markdown, scores
from evalia.engine.rules import Band, BandRule, RecordRule

FIX = Path(__file__).parent / "fixtures" / "synthetic"


@pytest.fixture(scope="module")
def doc():
    return load_pdf(FIX / "bid_northfield.pdf")


def test_quote_verified_only_on_its_own_page(doc):
    f = Finding(id="x", subject="s", kind="k", title="t", detail="d", basis="Fact", method="m",
                evidence=[Evidence(doc_id=doc.doc_id, page=4, quote="Experience Modification Rate")])
    assert verify_evidence(f, {doc.doc_id: doc}).fully_verified
    g = Finding(id="y", subject="s", kind="k", title="t", detail="d", basis="Fact", method="m",
                evidence=[Evidence(doc_id=doc.doc_id, page=2, quote="Experience Modification Rate")])
    g = verify_evidence(g, {doc.doc_id: doc})
    assert not g.fully_verified and g.basis == "Interpretation" and g.severity == "critical"


def test_invented_quote_is_not_verified(doc):
    f = Finding(id="x", subject="s", kind="k", title="t", detail="d", basis="Fact", method="m",
                evidence=[Evidence(doc_id=doc.doc_id, page=3, quote="Elm Street Distribution Center warehouse Exceptional")])
    assert not verify_evidence(f, {doc.doc_id: doc}).fully_verified


RULE = RecordRule(id="C1", title="Relevant", keyword_field="t", keywords=["warehouse"], year_field="y", year_min=2018,
                  year_max=2026, value_field="v", value_min=11_000_000, rating_field="r",
                  rating_scale=["Unsatisfactory", "Marginal", "Satisfactory", "Very Good", "Exceptional"],
                  rating_min="Satisfactory", role_field="role", role_required="Prime contractor",
                  points_per_record=2.5, max_records=2)


def test_record_rule_reasons():
    ok = {"t": "warehouse", "y": 2021, "v": 12e6, "r": "Very Good", "role": "Prime contractor"}
    assert RULE.check(ok) == []
    assert len(RULE.check({**ok, "v": 9.2e6, "y": 2016})) == 2
    assert "below the minimum" in RULE.check({**ok, "r": "Marginal"})[0]
    assert "not evidenced" in RULE.check({**ok, "r": None})[0]
    assert "is not 'Prime contractor'" in RULE.check({**ok, "role": "Subcontractor (steel package)"})[0]


def test_band_rule():
    b = BandRule(id="C2", title="EMR", field="emr", bands=[Band(up_to=0.85, points=5), Band(up_to=1.0, points=3), Band(up_to=None, points=0)])
    assert [b.points_for(x) for x in (0.78, 0.85, 0.95, 1.12)] == [5, 5, 3, 0]


def test_decision_requires_reason_and_evaluator():
    with pytest.raises(ValueError):
        Decision(finding_id="x", action="reject", evaluator="A. Evaluator")
    with pytest.raises(ValueError):
        Decision(finding_id="x", action="accept", evaluator=" ")
    Decision(finding_id="x", action="accept", evaluator="A. Evaluator")


def _f(i, pts, subject="A"):
    return Finding(id=i, subject=subject, criterion="C1", kind="record", title=i, detail="", basis="Fact", method="m", proposed_points=pts)


def test_scores_use_decisions_and_cap():
    fs = [_f("a", 2.5), _f("b", 2.5), _f("c", 2.5), _f("d", 0.0)]
    ev = "E. Valuator"
    ds = {"a": Decision(finding_id="a", action="accept", evaluator=ev),
          "b": Decision(finding_id="b", action="reject", reason="not comparable", evaluator=ev),
          "c": Decision(finding_id="c", action="accept", evaluator=ev),
          "d": Decision(finding_id="d", action="modify", reason="owner letter found later", modified_points=2.5, evaluator=ev)}
    assert final_points(fs[1], ds["b"]) == 0.0
    assert scores(fs, ds, {"C1": ("Relevant", 5.0)}) == {"A": {"C1": 5.0}}  # 7.5 capped at 5


def test_report_refuses_undecided_findings():
    with pytest.raises(ValueError):
        build_markdown(context={"title": "t", "reference": "r", "owner": "o"}, signoff={"by": "x", "at": "now"},
                       findings=[_f("a", 2.5)], decisions={}, caps={"C1": ("Relevant", 5.0)}, not_assessed=[],
                       inputs=[], model_calls=[], methods=set())


def test_residency_fails_closed(tmp_path):
    prof = Profile(name="p", provider="anthropic", model="m", residency="us_api", region="us", api_key_env="NOPE")
    with pytest.raises(ResidencyRefused):
        Gateway(prof, ResidencyPolicy(allowed=["self_hosted"]), tmp_path)
    assert not Gateway(prof, ResidencyPolicy(allowed=["us_api"]), tmp_path).available
