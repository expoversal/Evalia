# app/auth/switch.py
@router.post("/auth/switch-envelope")
async def switch_envelope(
    body: SwitchBody,                    # {tender_id, to_envelope, mfa_code}
    user: Claims = Depends(current_user),
):
    if Role(user.role) != Role.EVALUATION_LEAD:
        raise HTTPException(403)
    if not await _verify_stepup_mfa(user.sub, body.mfa_code):
        raise HTTPException(401, "step-up MFA required to switch envelope")
    # switching FROM technical TO commercial requires technical to be sealed
    if user.envelope_scope == "technical" and body.to_envelope == "commercial":
        if not await _envelope_sealed(body.tender_id, "technical"):
            raise HTTPException(423, "cannot switch to commercial before technical seal")
    async with db.transaction() as tx:
        await append_audit(tx, body.tender_id, body.to_envelope, user.sub,
                           "reveal_attempt", None, None,
                           {"from": user.envelope_scope, "to": body.to_envelope}, None)
    new_claims = Claims(**{**user.model_dump(),
                           "envelope_scope": body.to_envelope})
    return {"token": issue(new_claims, settings.JWT_SECRET)}
