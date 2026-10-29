import re

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()

def verify_evidence(score: CriterionScore, chunks) -> CriterionScore:
    text_by_doc = {c.doc_id: _norm(c.text) for c in chunks}
    kept = []
    for ev in score.evidence:
        source = text_by_doc.get(ev.doc_id, "")
        if _norm(ev.quote) and _norm(ev.quote) in source:
            kept.append(ev)
        else:
            score.missing_info.append(f"unverified quote: {ev.quote[:60]}")
    if len(kept) < len(score.evidence):
        score.confidence = "low"
    score.evidence = kept
    return score
