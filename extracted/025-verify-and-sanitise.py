def verify_and_sanitise(row: ComplianceRow, excerpts: list[Excerpt]) -> ComplianceRow:
    text_by_loc = {(e.doc_id, e.page): _norm(e.text) for e in excerpts}

    verified = []
    for ev in row.evidence:
        src = text_by_loc.get((ev.doc_id, ev.page), "")
        if _norm(ev.quote) and _norm(ev.quote) in src:
            verified.append(ev)
        else:
            row.evaluator_flag = "needs_clarification"
    row.evidence = verified

    # status sanity
    if row.status in ("compliant", "partial", "non_compliant") and not row.evidence:
        row.status = "not_addressed"
        row.evaluator_flag = "needs_clarification"
        row.confidence = "low"

    if row.status == "not_addressed" and not row.gap_note:
        row.confidence = "low"      # absence with no enumeration = untrustworthy

    if row.status == "compliant" and row.confidence == "low":
        row.evaluator_flag = "needs_clarification"

    return row
