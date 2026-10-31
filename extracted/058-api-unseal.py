class UnsealBody(BaseModel):
    reason: str
    co_signer_email: str
    co_signer_mfa: str

@router.post("/tenders/{tender_id}/{envelope}/unseal")
async def unseal(
    tender_id: str, envelope: str, body: UnsealBody,
    user: Claims = Depends(current_user),
):
    if Role(user.role) not in UNSEAL_ROLES:
        raise HTTPException(403)
    co = await db.fetchrow(
        "SELECT id, role FROM core.users WHERE email = $1 AND active",
        body.co_signer_email)
    if not co or Role(co["role"]) != Role.PROCUREMENT_OFFICER:
        raise HTTPException(403, "co-signer must be an active procurement_officer")
    if not await _verify_stepup_mfa(co["id"], body.co_signer_mfa):
        raise HTTPException(401, "co-signer MFA failed")
    if body.reason.strip() == "":
        raise HTTPException(400, "unseal reason required")

    schema = envelope
    async with db.transaction() as tx:
        seal = await tx.fetchrow(f"""
            SELECT * FROM {schema}.seals
            WHERE tender_id = $1 AND revoked_at IS NULL FOR UPDATE
        """, tender_id)
        if not seal:
            raise HTTPException(404, "no active seal")
        await tx.execute(f"""
            UPDATE {schema}.seals
            SET revoked_at = now(), revoked_by = $1, revoke_reason = $2
            WHERE id = $3
        """, user.sub, f"{body.reason} (co-signed by {co['id']})", seal["id"])
        await append_audit(tx, tender_id, envelope, user.sub, "unseal",
                           f"{schema}.seals", seal["id"],
                           _jsonable(dict(seal)),
                           {"reason": body.reason, "co_signer": str(co["id"])})
    return {"ok": True}
