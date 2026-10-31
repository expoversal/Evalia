# app/api/matrix.py
@router.get("/tenders/{tender_id}/{envelope}/matrix")
async def get_matrix(
    tender_id: str,
    envelope: str,
    bidder_id: str | None = None,
    user: Claims = Depends(require_read(path_envelope := "dynamic")),
):
    # path_envelope comes from the path param; FastAPI validates the literal
    if envelope not in ("technical", "commercial"):
        raise HTTPException(400)
    await require_read(envelope)(user, tender_id)

    schema = envelope
    rows = await db.fetch(f"""
        SELECT cr.id::text, cr.bidder_id::text, b.name AS bidder_name,
               req.clause_ref, req.requirement_text, req.mandatory,
               req.category, req.conditional, req.condition,
               cr.ai_status, cr.ai_confidence, cr.ai_flag,
               cr.ai_evidence::text AS ai_evidence,
               cr.ai_gap_note,
               cr.human_status, cr.human_note, cr.override_reason,
               cr.human_actor::text, cr.human_decided_at::text
        FROM {schema}.compliance_rows cr
        JOIN core.requirements req ON req.id = cr.requirement_id
        JOIN core.bidders b ON b.id = cr.bidder_id
        WHERE cr.tender_id = $1
          AND ($2::uuid IS NULL OR cr.bidder_id = $2::uuid)
        ORDER BY
          -- unreviewed mandatory non-compliances first
          (cr.human_status IS NULL) DESC,
          (req.mandatory AND COALESCE(cr.human_status, cr.ai_status)
              IN ('non_compliant','not_addressed')) DESC,
          req.mandatory DESC,
          req.clause_ref,
          b.name
    """, tender_id, bidder_id)
    return {
        "envelope": envelope,
        "sealed": await _envelope_sealed(tender_id, envelope),
        "rows": [ {**dict(r), "ai_evidence": json.loads(r["ai_evidence"])}
                  for r in rows ],
    }
