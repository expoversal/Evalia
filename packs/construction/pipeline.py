"""Run the whole evaluation on one request for proposal and its submissions, and package the result for the interface.

Nothing here is decided: the output is the set of proposed findings and the analyses that
do not depend on the evaluator's decisions. Scores that depend on decisions are computed
when the evaluator has decided.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from evalia.engine.documents import load_pdf
from evalia.engine.verify import quote_on_page

from .evaluate import evaluate_all, load_framework
from .rfp import read_rfp
from .submission import read_submission


def run(rfp_path: Path, tender_paths: list[Path], receipts_path: Path) -> dict:
    fw = load_framework()
    rfp_doc = load_pdf(rfp_path)
    rfp = read_rfp(rfp_doc)
    form_titles = [f["form"] for f in rfp.forms]
    subs = []
    for path in tender_paths:
        doc = load_pdf(path)
        subs.append((read_submission(doc, form_titles), doc))
    receipts = {k: str(v) for k, v in yaml.safe_load(Path(receipts_path).read_text()).items()}
    result = evaluate_all(rfp, rfp_doc, subs, receipts, fw)

    register = [{**e.model_dump(), "verified": quote_on_page(rfp_doc, e.page, e.quote)} for e in rfp.entries]
    consistency = []
    published = {s["id"]: s.get("max") for s in fw.streams if s.get("scored")}
    for stream, pts in rfp.weights.items():
        consistency.append({"stream": stream, "rfp": pts, "framework": published.get(stream),
                            "match": published.get(stream) == pts})
    tenderers = []
    for s, doc in subs:
        key = doc.doc_id.removeprefix("tender_")
        tenderers.append({"key": key, "name": s.tenderer, "doc_id": doc.doc_id, "pages": len(doc.pages),
                          "sha256": doc.sha256, "received": receipts.get(key), "method": s.method,
                          "programme_weeks": s.programme_weeks, "deviations": len(s.deviations)})
    return {
        "context": {"reference": rfp.reference, "title": rfp.title, "employer": rfp.employer,
                    "deadline": receipts["deadline"], "deadline_text": rfp.deadline_text, "doc_id": rfp_doc.doc_id,
                    "pages": len(rfp_doc.pages), "sha256": rfp_doc.sha256},
        "register": register,
        "framework": {**fw.model_dump(mode="json"), "consistency": consistency,
                      "requirements": rfp.requirements, "key_roles": rfp.key_roles, "particulars": rfp.particulars},
        "tenderers": tenderers,
        "deviations": [{"tenderer": s.tenderer, **d.model_dump(),
                        "head": fw.risk_heads.get(d.particular, {}).get("head", "Unclassified"),
                        "material": fw.risk_heads.get(d.particular, {}).get("material", True)}
                       for s, _ in subs for d in s.deviations],
        "cashflow": {s.tenderer: s.cashflow for s, _ in subs},
        "findings": [f.model_dump(mode="json") for f in result["findings"]],
        "commercial": result["commercial"],
        "coverage": result["coverage"],
        "outliers": result["outliers"],
        "identical": result["identical"],
        "award": result["award"],
        "lot_prices": result["lot_prices"],
        "pages": {d.doc_id: {p.number: p.text for p in d.pages} for d in [rfp_doc] + [doc for _, doc in subs]},
    }
