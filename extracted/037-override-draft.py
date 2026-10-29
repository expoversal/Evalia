@router.post("/tenders/{tender_id}/compliance/{row_id}/override")
async def override_row(
    tender_id: str, row_id: str,
    body: OverrideBody,
    user: User = Depends(current_user),
):
    row = await get_row_or_404(row_id)
    envelope = "technical" if row_in_technical(row_id) else "commercial"
    await require_envelope(envelope, tender_id, user)

    # audit
    async with db.transaction() as tx:
        before = dict(row)
        await tx.execute(f"""
            UPDATE {envelope}.compliance_rows
            SET human_status = $1, human_note = $2, override_reason = $3,
                human_actor = $4, human_decided_at = now()
            WHERE id = $5
        """, body.status, body.note, body.reason, user.id, row_id)
        await append_audit(tx, tender_id, envelope, user.id, "override",
                           f"{envelope}.compliance_rows", row_id,
                           before, {**before, "human_status": body.status})
    return {"ok": True}
