class ComplianceRow(BaseModel):
    req_id: str
    status: Literal["compliant","partial","non_compliant","not_addressed"]
    evidence: list[Evidence]     # same verified-quote type as before
    gap_note: str | None

async def build_matrix(requirements, bid_chunks, retriever, llm):
    rows = []
    for req in requirements:
        hits = retriever.search(req.text, bid_doc_ids, k=8)
        if not hits:
            rows.append(ComplianceRow(req_id=req.req_id,
                                      status="not_addressed", evidence=[]))
            continue
        row = await llm.structured(..., schema=ComplianceRow)
        rows.append(verify_evidence(row, hits))
    return rows
