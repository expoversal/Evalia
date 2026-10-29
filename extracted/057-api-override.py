class OverrideBody(BaseModel):
    status: str
    note: str | None = None
    reason: str                     # required — must be non-empty
    expected_version: str           # the ai_proposed_at timestamp; optimistic lock

@router.post("/tenders/{tender_id}/{envelope}/rows/{row_id}/override")
async def override_row(
    tender_id: str, envelope: str, row_id: str,
    body: OverrideBody,
    user: Claims = Depends(current_user),
):
    await require_write(envelope)(user, tender_id)
    async with db.transaction() as tx:
        before = await tx.fetchrow(f"""
            SELECT * FROM {envelope}.compliance_rows
            WHERE id = $1 AND tender_id = $2 FOR UPDATE
        """, row_id, tender_id)
        if not before:
            raise HTTPException(404)
        # optimistic lock — prevents two evaluators racing
        if str(before["ai_proposed_at"]) != body.expected_version:
            raise HTTPException(409, "row was updated by another session; reload")
        await tx.execute(f"""
            UPDATE {envelope}.compliance_rows
            SET human_status = $1, human_note = $2, override_reason = $3,
                human_actor = $4, human_decided_at = now()
            WHERE id = $5
        """, body.status, body.note, body.reason, user.sub, row_id)
        after = dict(before)
        after["human_status"] = body.status
        after["override_reason"] = body.reason
        await append_audit(tx, tender_id, envelope, user.sub, "override",
                           f"{envelope}.compliance_rows", row_id,
                           _jsonable(dict(before)), _jsonable(after))
    return {"ok": True}

def _jsonable(d: dict) -> dict:
    return {k: (str(v) if hasattr(v, "isoformat") else v)
            for k, v in d.items()}
