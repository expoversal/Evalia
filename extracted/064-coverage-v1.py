@router.get("/tenders/{tender_id}/{envelope}/coverage")
async def coverage(tender_id: str, envelope: str,
                   user: Claims = Depends(require_read("dynamic"))):
    await require_read(envelope)(user, tender_id)
    row = await db.fetchrow(f"""
        SELECT
          COUNT(*) FILTER (WHERE human_status IS NULL) AS unreviewed,
          COUNT(*) FILTER (WHERE ai_flag = 'needs_clarification'
                              AND human_status IS NULL) AS needs_clarification,
          COUNT(*) AS total
        FROM {envelope}.compliance_rows WHERE tender_id = $1
    """, tender_id)
    return {**dict(row), "can_seal": row["unreviewed"] == 0}
