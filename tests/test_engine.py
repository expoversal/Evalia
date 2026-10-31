"""Engine tests on synthetic material only."""
from pathlib import Path

import pytest

from evalia.engine.documents import load_pdf
from evalia.engine.verify import find_quote
from evalia.engine.findings import Decision, Evidence, Finding, final_points, final_value, verify_evidence
from evalia.engine.llm import Gateway, Profile, ResidencyPolicy, ResidencyRefused
from evalia.engine.report import build_markdown, scores
from evalia.engine.rules import Band, BandRule, RecordRule
from evalia.engine.scoring import (apply_correction_rule, cheapest_award, deviations_from_median, front_loading,
                                   identical_values, price_scores, sensitivity)

FIX = Path(__file__).parent / "fixtures" / "synthetic"


@pytest.fixture(scope="module")
def doc():
    return load_pdf(FIX / "tender_northfield.pdf")


def test_quote_verified_only_on_its_own_page(doc):
    page = find_quote(doc, "Experience Modification Rate")
    f = Finding(id="x", subject="s", kind="k", title="t", detail="d", basis="Fact", method="m",
                evidence=[Evidence(doc_id=doc.doc_id, page=page, quote="Experience Modification Rate")])
    assert verify_evidence(f, {doc.doc_id: doc}).fully_verified
    g = Finding(id="y", subject="s", kind="k", title="t", detail="d", basis="Fact", method="m",
                evidence=[Evidence(doc_id=doc.doc_id, page=page - 1, quote="Experience Modification Rate")])
    g = verify_evidence(g, {doc.doc_id: doc})
    assert not g.fully_verified and g.basis == "Interpretation" and g.severity == "critical"


def test_invented_quote_is_not_verified(doc):
    f = Finding(id="x", subject="s", kind="k", title="t", detail="d", basis="Fact", method="m",
                evidence=[Evidence(doc_id=doc.doc_id, page=find_quote(doc, "Bayfront Suites Renovation"),
                                   quote="Bayfront Suites Renovation hotel fit-out Exceptional")])
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
    with pytest.raises(ValueError):
        Decision(finding_id="x", action="score", reason="clear method", evaluator="A. Evaluator")
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
    assert scores(fs, ds, {"C1": {"title": "Relevant", "max": 5.0}}) == {"A": {"C1": 5.0}}  # 7.5 capped at 5


def test_scores_with_base_deductions_and_evaluator_score():
    ev = "E. Valuator"
    k = [Finding(id=i, subject="A", criterion="K1", kind="deviation", title=i, detail="", basis="Fact", method="m",
                 proposed_points=-3.0) for i in ("k1", "k2", "k3", "k4")]
    j = Finding(id="j", subject="A", criterion="T2", kind="judgement", title="j", detail="", basis="Interpretation",
                method="evaluator", score_max=10.0)
    ds = {f.id: Decision(finding_id=f.id, action="accept", evaluator=ev) for f in k}
    ds["j"] = Decision(finding_id="j", action="score", reason="covers seven of eight requirements", modified_points=7.0, evaluator=ev)
    crit = {"K1": {"title": "Contract", "max": 10, "base": 10}, "T2": {"title": "Methodology", "max": 10}}
    assert scores(k + [j], ds, crit) == {"A": {"K1": 0.0, "T2": 7.0}}  # 10 - 12 floored at 0
    del ds["k4"], ds["k3"]
    assert scores(k + [j], ds, crit)["A"]["K1"] == 4.0  # undecided deductions do not count


def test_final_value():
    f = Finding(id="p", subject="A", kind="price", title="p", detail="", basis="Fact", method="m", value=100.0)
    assert final_value(f, None) is None
    assert final_value(f, Decision(finding_id="p", action="accept", evaluator="E")) == 100.0
    assert final_value(f, Decision(finding_id="p", action="modify", reason="clarified", modified_value=90.0, evaluator="E")) == 90.0
    assert final_value(f, Decision(finding_id="p", action="reject", reason="wrong", evaluator="E")) is None


def test_scoring_functions():
    assert apply_correction_rule(100, 120, "lower_of_stated_and_corrected") == 100
    assert apply_correction_rule(130, 120, "lower_of_stated_and_corrected") == 120
    assert price_scores({"a": 100, "b": 125}, 50) == {"a": 50.0, "b": 40.0}
    assert deviations_from_median({"a": 10, "b": 12, "c": 15}) == pytest.approx({"a": -1 / 6, "b": 0.0, "c": 0.25})
    assert identical_values({"a": {"x": 1, "y": 2, "z": 3}, "b": {"x": 1, "y": 2, "z": 4}}, 2) == [("a", "b", ["x", "y"])]
    assert front_loading([10, 10, 30, 50], 0.5) == 0.2
    award = cheapest_award({"a": {"A": 10, "B": 9}, "b": {"A": 11, "B": 7}}, {"a": 18.5, "b": 17.5})
    assert award["split"] == {"A": "a", "B": "b"} and award["split_cost"] == 17 and award["combined"] == "b"
    sens = sensitivity({"a": {"t": 40, "c": 30}, "b": {"t": 20, "c": 50}}, {"t": 40, "c": 50},
                       {"quality": {"t": 60, "c": 40}, "price": {"t": 20, "c": 80}})
    assert sens["quality"]["ranking"] == ["a", "b"] and sens["price"]["ranking"] == ["b", "a"]


def test_report_refuses_undecided_findings():
    with pytest.raises(ValueError):
        build_markdown(context={"title": "t", "reference": "r", "owner": "o"}, signoff={"by": "x", "at": "now"},
                       findings=[_f("a", 2.5)], decisions={}, criteria={"C1": {"title": "Relevant", "max": 5.0}}, not_assessed=[],
                       inputs=[], model_calls=[], methods=set())


def test_residency_fails_closed(tmp_path):
    prof = Profile(name="p", provider="anthropic", model="m", residency="us_api", region="us", api_key_env="NOPE")
    with pytest.raises(ResidencyRefused):
        Gateway(prof, ResidencyPolicy(allowed=["self_hosted"]), tmp_path)
    assert not Gateway(prof, ResidencyPolicy(allowed=["us_api"]), tmp_path).available


def test_words_to_number():
    from evalia.engine.numbers import words_to_number
    assert words_to_number("Nineteen million five hundred fifty-six thousand dollars") == 19_556_000
    assert words_to_number("Seventeen million six hundred two thousand two hundred dollars") == 17_602_200
    assert words_to_number("One hundred and five") == 105
    assert words_to_number("about ten") is None
