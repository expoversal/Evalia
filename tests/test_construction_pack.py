"""End-to-end checks of the construction pack on the fictional request for proposal and tenders."""
from pathlib import Path

import pytest

from evalia.engine.documents import load_pdf
from evalia.engine.findings import Decision
from evalia.engine.llm import Gateway, Profile, ResidencyPolicy
from evalia.engine.report import build_markdown, scores
from evalia.engine.verify import find_quote
from packs.construction.evaluate import _Sink, check_technical, load_framework
from packs.construction.extract import extract_with_model
from packs.construction.pipeline import run
from packs.construction.rfp import read_rfp
from packs.construction.submission import read_submission

FIX = Path(__file__).parent / "fixtures" / "synthetic"
FW = load_framework()
N, C, H = "Northfield Builders Inc. (fictional)", "Cobalt Ridge Construction LLC (fictional)", "Harbor & Pine Contractors (fictional)"


@pytest.fixture(scope="module")
def out():
    return run(FIX / "rfp_LG-2026-031.pdf", [FIX / f"tender_{k}.pdf" for k in ("northfield", "cobalt", "harborpine")],
               FIX / "receipts.yaml")


def of(out, subject, check=None, stream=None):
    return [f for f in out["findings"] if f["subject"] == subject and (check is None or f["check"] == check)
            and (stream is None or f["stream"] == stream)]


def test_every_quote_verifies(out):
    assert all(r["verified"] for r in out["register"])
    assert all(e["verified"] for f in out["findings"] for e in f["evidence"])


def test_rfp_register_and_framework_consistency(out):
    keys = {r["key"] for r in out["register"]}
    assert {"Deadline", "Validity", "Weights", "Arithmetic", "ER-01", "ER-08", "Delay damages"} <= keys
    assert all(c["match"] for c in out["framework"]["consistency"])
    assert [k["role"] for k in out["framework"]["key_roles"]] == ["Project Manager", "Site Manager", "HSE Manager", "BIM Coordinator"]


def test_receipt_late_tender(out):
    assert "6 minutes after the deadline" in of(out, H, "Receipt time")[0]["title"]
    assert of(out, N, "Receipt time")[0]["severity"] == "info"


def test_gate(out):
    assert all(f["severity"] == "info" for f in of(out, N, stream="gate"))
    cobalt = {f["check"]: f for f in of(out, C, stream="gate")}
    assert cobalt["Power of attorney"]["severity"] == "critical"
    assert "90 days" in cobalt["Validity period"]["title"]
    assert "$150,000.00 instead of $250,000.00" in cobalt["Provisional sums"]["title"]
    assert "simultaneously" in cobalt["Qualifications outside Form G"]["evidence"][0]["quote"]
    assert "asbestos" in of(out, H, "Qualifications outside Form G")[0]["evidence"][0]["quote"]


def test_technical(out):
    assert out["coverage"][N] == {f"ER-0{i}": "addressed" for i in range(1, 9)}
    assert out["coverage"][H]["ER-03"] == "contradicted" and out["coverage"][H]["ER-08"] == "contradicted"
    assert out["coverage"][C]["ER-01"] == "not addressed"
    sub = of(out, H, "T5 Claims substantiated")
    assert len(sub) == 1 and "Ironwood" in sub[0]["title"] and "'Marginal'" in sub[0]["detail"]
    assert [f["proposed_points"] for f in of(out, C, "T6 Key personnel")] == [1.25, 0.0, 1.25, 0.0]
    assert of(out, N, "T2 Methodology score")[0]["score_max"] == 10


def test_commercial(out):
    c = out["commercial"][C]
    assert c["combined_stated"] == 17_602_200 and c["combined_corrected"] == 17_780_400
    assert c["evaluated"] == 17_702_200  # stated stands under the lower-of rule, plus $100,000 provisional sum restored
    assert "under-extended by $180,000.00" in of(out, C, "Arithmetic")[0]["title"]
    assert "front-loaded" in of(out, C, "Cash flow profile")[0]["title"]
    assert {f["title"].split(" (")[0] for f in of(out, C, "Rate outliers")} == {"Lot A item 1", "Lot B item 1"}
    assert out["award"]["split"] == {"A": C, "B": N} and out["award"]["combined"] == C
    assert out["award"]["split_cost"] - out["award"]["combined_cost"] == pytest.approx(151_800)


def test_contract(out):
    dd = [f for f in of(out, C, "Contract deviations") if "Delay damages" in f["title"]][0]
    assert dd["proposed_points"] == -3 and "a reduction of $885,110.00" in dd["detail"]
    assert of(out, N, "Contract deviations")[0]["proposed_points"] == -1
    assert of(out, H, "Contract deviations")[0]["proposed_points"] == 0


def test_integrity(out):
    assert out["identical"][0]["items"] == ["Lot A item 2", "Lot A item 3", "Lot B item 2", "Lot B item 3", "Lot B item 6"]
    assert of(out, H, "Litigation")[0]["severity"] == "attention"
    assert of(out, C, "Shared subcontractors") and not of(out, N, "Shared subcontractors")


def test_full_review_scores_and_report(out):
    from evalia.engine.findings import Finding
    fs = [Finding.model_validate(f) for f in out["findings"]]
    ev = "E. Valuator (fictional)"
    ds = {f.id: (Decision(finding_id=f.id, action="score", reason="test score", modified_points=8.0, evaluator=ev)
                 if f.score_max else Decision(finding_id=f.id, action="accept", evaluator=ev)) for f in fs}
    crit = {c["id"]: c for c in out["framework"]["criteria"] if c["id"] != "P1"}
    table = scores(fs, ds, crit)
    assert table[N] == {"T1": 5, "T2": 8, "T3": 5, "T4": 5, "T5": 10, "T6": 5, "K1": 9}
    assert table[C]["K1"] == 4 and table[H]["T3"] == 0 and table[H]["T5"] == 5
    md = build_markdown(context={"title": "t", "reference": "r", "owner": "o"}, signoff={"by": "x", "at": "now"},
                        findings=fs, decisions=ds, criteria=crit, not_assessed=FW.not_assessed, inputs=[],
                        model_calls=[], methods={"form reader"})
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
    rfp = read_rfp(load_pdf(FIX / "rfp_LG-2026-031.pdf"))
    doc = load_pdf(FIX / "tender_harborpine.pdf")
    k = find_quote(doc, "Clearwater Harbour Hotel hotel fit-out")
    reading = {
        "projects": [
            {"name": "Clearwater Harbour Hotel", "building_type": "hotel fit-out", "owner": "Clearwater Hotels",
             "completed": 2021, "contract_value": 11900000, "role": "Prime contractor", "claimed_rating": "Very Good", "page": k,
             "quote": "1 Clearwater Harbour Hotel hotel fit-out Clearwater Hotels 2021 $11,900,000.00 Prime contractor Very Good"},
            # Invented by the "model": a value and a quote that are not on the page.
            {"name": "Silver Lake Lodge Renovation", "building_type": "hotel fit-out", "owner": "Silver Lake Resorts",
             "completed": 2024, "contract_value": 16600000, "role": "Prime contractor", "claimed_rating": "Satisfactory", "page": k,
             "quote": "4 Silver Lake Lodge Renovation hotel fit-out Silver Lake Resorts 2024 $16,600,000.00 Prime contractor Satisfactory"},
        ],
        "ratings": [{"project_name": "Clearwater Harbour Hotel", "rating": "Very Good", "page": k,
                     "quote": "Overall performance rating: Very Good"}],
    }
    s = read_submission(doc, [f["form"] for f in rfp.forms])
    m = extract_with_model(doc, FakeGateway(tmp_path, reading))
    s.projects, s.ratings = m.projects, m.ratings
    found = []
    check_technical(rfp, s, doc, _Sink("hp", s.tenderer, {doc.doc_id: doc}, "AI model (fake)", found), FW)
    silver = [f for f in found if f.check == "T5 Relevant experience" and "Silver Lake" in f.title][0]
    assert not silver.fully_verified and silver.basis == "Interpretation" and silver.severity == "critical"
    clear = [f for f in found if f.check == "T5 Relevant experience" and "Clearwater" in f.title][0]
    assert not clear.fully_verified  # the rating quote was cited on the wrong page


def test_tender_document_contradictions(out):
    issues = {i["key"]: [v["value"] for v in i["values"]] for i in out["rfp_issues"]}
    assert issues == {"Tender validity (days)": ["120", "90"], "Tender security validity (days)": ["150", "120"]}
    assert all(v["verified"] for i in out["rfp_issues"] for v in i["values"])


def test_new_responsiveness_checks(out):
    assert "valid for 90 days, not the 150 required" in of(out, C, "Tender security")[0]["title"]
    assert of(out, C, "Addenda acknowledged")[0]["title"] == "Addendum No. 2 not acknowledged"
    assert of(out, H, "No prices in technical tender")[0]["severity"] == "attention"
    assert of(out, N, "No prices in technical tender")[0]["severity"] == "info"


def test_words_prevail_and_preference(out):
    assert of(out, H, "Words and figures")[0]["severity"] == "critical"
    assert out["commercial"][H]["evaluated"] == 19_556_000  # words prevail over $19,565,000 in figures
    assert out["commercial"][C]["comparison"] == pytest.approx(17_702_200 * 1.05)  # registered outside the home state
    assert out["commercial"][N]["comparison"] == out["commercial"][N]["evaluated"]
    assert out["rules"]["technical_pass"] == 24 and out["rules"]["methodology_cutoff"] == 4


def test_qualification(out):
    assert "expired on 31 August 2026" in of(out, H, "Tax clearance certificate")[0]["title"]
    assert of(out, H, "Financial standing")[0]["severity"] == "critical"
    assert of(out, N, "Financial standing")[0]["severity"] == "info"


def test_dossier_and_opening(out):
    assert [(x["annex"], x["title"]) for x in out["rfp_missing"]] == [("4", "Drawings")]
    assert all(f["severity"] == "info" for f in out["findings"] if f["check"] in ("One tender per tenderer", "Letter of authority at opening"))


def test_further_responsiveness(out):
    assert of(out, C, "Site visit")[0]["severity"] == "critical" and of(out, N, "Site visit")[0]["severity"] == "info"
    assert "Lakeline Services" in of(out, H, "Documents for each entity")[0]["title"]
    assert "sales tax not stated separately" in of(out, C, "Currency and tax")[0]["title"]
    assert of(out, N, "Page limits")[0]["severity"] == "info"
    assert of(out, N, "Alternatives")[0]["title"] == "No alternative tender"


def test_further_technical_and_commercial(out):
    assert of(out, C, "Plant")[0]["title"] == "Plant short: Scissor lift (3 of 4); Goods hoist (0 of 1)"
    stc = [f for f in of(out, H, "Specification values") if "STC" in f["title"]][0]
    assert stc["severity"] == "critical" and "minimum 55" in stc["title"]
    assert "below the 30% required" in of(out, H, "Local workforce")[0]["title"]
    assert all(f["severity"] == "info" for f in out["findings"] if f["check"] in ("Letter against schedules", "Unpriced items"))


def test_further_qualification(out):
    assert "2025 missing" in of(out, C, "Accounts")[0]["title"]
    assert "Pine Street Builders 20%" in of(out, H, "Joint-venture shares")[0]["title"]
    assert out["owners"] == [{"a": C, "b": H, "owner": "Marcus Ellery (fictional)"}]
    assert of(out, C, "Shared ownership")[0]["severity"] == "critical"
