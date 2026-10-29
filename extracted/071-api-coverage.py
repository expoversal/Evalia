# app/api/coverage.py
@router.get("/tenders/{tender_id}/{envelope}/coverage")
async def coverage(
    tender_id: str, envelope: str,
    user: Claims = Depends(current_user),
):
    await require_read(envelope)(user, tender_id)
    row = await db.fetchrow(f"""
        WITH c AS (
          SELECT
            COUNT(*) FILTER (WHERE human_status IS NULL) AS unreviewed,
            COUNT(*) FILTER (WHERE ai_flag = 'needs_clarification'
                              AND human_status IS NULL) AS needs_clarification,
            COUNT(*) FILTER (WHERE human_status IS NOT NULL
                              AND ai_status <> human_status) AS overrides,
            COUNT(*) AS total
          FROM {envelope}.compliance_rows WHERE tender_id = $1
        ),
        s AS (
          SELECT COUNT(*) FILTER (WHERE human_score IS NULL) AS scores_unreviewed,
                 COUNT(*) AS scores_total
          FROM {envelope}.criterion_scores WHERE tender_id = $1
        )
        SELECT c.*, s.scores_unreviewed, s.scores_total
        FROM c, s
    """, tender_id)
    return {
        **dict(row),
        "can_seal": row["unreviewed"] == 0 and row["scores_unreviewed"] == 0,
    }
