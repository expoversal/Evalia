@router.post("/tenders/{tender_id}/{envelope}/unseal")
async def unseal(
    tender_id: str, envelope: str,
    body: UnsealBody,     # {reason, threshold_auth, procurement_mfa}
    user: Claims = Depends(current_user),
):
    if Role(user.role) not in UNSEAL_ROLES:
        raise HTTPException(403)

    # 1. Verify the threshold signature on the unseal authorisation
    auth = body.threshold_auth
    if auth["action"] != "unseal" or auth["tender_id"] != tender_id \
       or auth["envelope"] != envelope:
        raise HTTPException(400, "authorisation does not match request")
    auth_bytes = json.dumps(
        {k: v for k, v in auth.items() if k not in ("signature", "signer_key_id")},
        sort_keys=True, separators=(",", ":")).encode()
    if not verify_threshold_signature(
        base64.b64decode(auth["signature"]), auth_bytes,
        await load_unseal_group_pubkey()
    ):
        raise HTTPException(401, "threshold signature invalid")

    # 2. Verify the procurement officer's co-signature (FIDO2 MFA)
    if not await verify_procurement_mfa(body.procurement_mfa, auth):
        raise HTTPException(401, "procurement co-signature invalid")

    # 3. Verify the authorised signers were who they claimed
    #    (each participant_id maps to a real executive; audit trail required)
    for pid in auth["signers"]:
        if pid not in await current_quorum_members(tender_id):
            raise HTTPException(403, f"signer {pid} not authorised for this tender")

    # 4. Proceed with unseal — the rest is as in Part 9 of the previous build
    ...
