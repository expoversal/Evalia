@router.get("/tenders/{tender_id}/{envelope}/rows/{row_id}")
async def get_row(tender_id: str, envelope: str, row_id: str,
                  user: Claims = Depends(current_user)):
    await require_read(envelope)(user, tender_id)
    row = await db.fetchrow(f"""
        SELECT cr.*, req.clause_ref, req.requirement_text, req.evidence_expected,
               b.name AS bidder_name, b.bundle_key
        FROM {envelope}.compliance_rows cr
        JOIN core.requirements req ON req.id = cr.requirement_id
        JOIN core.bidders b ON b.id = cr.bidder_id
        WHERE cr.id = $1 AND cr.tender_id = $2
    """, row_id, tender_id)
    if not row:
        raise HTTPException(404)
    # log view
    async with db.transaction() as tx:
        await append_audit(tx, tender_id, envelope, user.sub, "view",
                           f"{envelope}.compliance_rows", row_id, None, None)
    return dict(row)
