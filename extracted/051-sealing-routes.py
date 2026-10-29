# app/sealing/routes.py
@router.post("/tenders/{tender_id}/seal/{envelope}")
async def seal_envelope(
    tender_id: str,
    envelope: str,
    user: Claims = Depends(current_user),
):
    if Role(user.role) not in SEAL_ROLES:
        raise HTTPException(403, "only evaluation_lead may seal")
    if envelope == "commercial" and not await _envelope_sealed(tender_id, "technical"):
        raise HTTPException(423, "cannot seal commercial before technical")

    schema = "technical" if envelope == "technical" else "commercial"

    # 1. Fetch the canonical snapshot
    if envelope == "technical":
        rows = await db.fetch("""
            SELECT cr.bidder_id::text, cr.requirement_id::text,
                   cr.ai_status, cr.ai_confidence, cr.ai_evidence::text,
                   cr.ai_flag, cr.ai_model, cr.ai_prompt_hash,
                   COALESCE(cr.human_status, 'unreviewed') AS human_status,
                   cr.human_note, cr.override_reason,
                   cr.human_actor::text, cr.human_decided_at::text
            FROM technical.compliance_rows cr
            WHERE cr.tender_id = $1
            ORDER BY cr.bidder_id, cr.requirement_id
        """, tender_id)
        scores = await db.fetch("""
            SELECT bidder_id::text, criterion_id::text,
                   ai_score::text, ai_rationale, ai_confidence,
                   human_score::text, override_reason,
                   human_actor::text, human_decided_at::text
            FROM technical.criterion_scores
            WHERE tender_id = $1
            ORDER BY bidder_id, criterion_id
        """, tender_id)
        snapshot = {"compliance": [dict(r) for r in rows],
                    "scores": [dict(r) for r in scores]}
    else:
        bq = await db.fetch("""
            SELECT bidder_id::text, issue_type, item_code, detail::text
            FROM commercial.bq_checks WHERE tender_id = $1
            ORDER BY bidder_id, issue_type, item_code
        """, tender_id)
        alt = await db.fetch("""
            SELECT bidder_id::text, item_code, rate::text,
                   median_rate::text, pct_of_median::text
            FROM commercial.alt_flags WHERE tender_id = $1
            ORDER BY bidder_id, item_code
        """, tender_id)
        snapshot = {"bq_checks": [dict(r) for r in bq],
                    "alt_flags": [dict(r) for r in alt]}

    # 2. Seal
    prev = await db.fetchrow(f"""
        SELECT id::text FROM {schema}.seals
        WHERE tender_id = $1 AND revoked_at IS NULL
        ORDER BY signed_at DESC LIMIT 1
    """, tender_id)
    sealed = sign_seal(
        rows=_flatten_for_merkle(snapshot),
        tender_id=tender_id, envelope=envelope,
        prev_seal_id=prev["id"] if prev else None,
        signer_key_id=settings.SEAL_KEY_ID,
        key=await kms.get_ed25519_private_key(settings.SEAL_KEY_ID),
    )

    # 3. Persist + audit atomically
    async with db.transaction() as tx:
        seal_id = await tx.fetchval(f"""
            INSERT INTO {schema}.seals
              (tender_id, envelope, merkle_root, leaf_count, snapshot,
               signature, signer_key_id, signed_by, signed_at, prev_seal_id)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6,$7,$8,$9,$10)
            RETURNING id
        """, tender_id, envelope, sealed.merkle_root, sealed.leaf_count,
             json.dumps(snapshot), sealed.signature, sealed.signer_key_id,
             user.sub, sealed.signed_at,
             sealed.prev_seal_id)
        await tx.execute("""
            UPDATE core.tenders
            SET state = CASE
                WHEN $2 = 'technical' THEN 'tech_sealed'
                WHEN $2 = 'commercial' THEN 'commercial_sealed'
            END
            WHERE id = $1
        """, tender_id, envelope)
        await append_audit(tx, tender_id, envelope, user.sub, "seal",
                           f"{schema}.seals", seal_id,
                           None, asdict(sealed))
    return {"seal_id": seal_id, "merkle_root": sealed.merkle_root}
