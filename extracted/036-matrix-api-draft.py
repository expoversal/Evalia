@router.get("/tenders/{tender_id}/envelope/{envelope}/matrix")
async def get_matrix(
    tender_id: str,
    envelope: str,
    bidder_id: str | None = None,
    user: User = Depends(current_user),
):
    await require_envelope(envelope, tender_id, user)
    schema = "technical" if envelope == "technical" else "commercial"
    rows = await db.fetch_all(f"""
        SELECT r.id, req.clause_ref, req.requirement_text, req.mandatory,
               r.status AS ai_status, r.human_status, r.ai_confidence,
               r.evidence, r.gap_note, r.evaluator_flag,
               b.name AS bidder_name, r.bidder_id
        FROM {schema}.compliance_rows r
        JOIN core.requirements req ON req.id = r.requirement_id
        JOIN core.bidders b ON b.id = r.bidder_id
        WHERE r.tender_id = $1
          AND ($2::uuid IS NULL OR r.bidder_id = $2)
        ORDER BY (r.human_status IS NULL AND r.ai_status IN ('non_compliant','not_addressed')) DESC,
                 req.mandatory DESC,
                 req.clause_ref
    """, tender_id, bidder_id)
    return rows
