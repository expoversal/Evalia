class ConfirmBody(BaseModel):
    run_id: str
    accepted: bool
    note: str | None = None

@router.post("/tenders/{tender_id}/award/confirm")
async def confirm_award(
    tender_id: str, body: ConfirmBody,
    user: Claims = Depends(current_user),
):
    if Role(user.role) != Role.PROCUREMENT_OFFICER:
        raise HTTPException(403, "only procurement_officer may confirm award")

    run = await db_award.fetchrow(
        "SELECT * FROM award.runs WHERE id = $1 AND tender_id = $2",
        body.run_id, tender_id)
    if not run:
        raise HTTPException(404)

    async with db_award.transaction() as tx:
        await tx.execute("""
            UPDATE core.tenders SET state = 'awarded' WHERE id = $1
        """, tender_id)
        await append_audit(tx, tender_id, None, user.sub,
                           "award_confirm" if body.accepted else "award_reject",
                           "award.runs", body.run_id, None,
                           {"accepted": body.accepted,
                            "note": body.note,
                            "report_hash": run["report_hash"]})
    return {"ok": True, "state": "awarded" if body.accepted else "award_rejected"}
