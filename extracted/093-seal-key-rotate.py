# app/sealing/rotate.py — run in a planned change window
async def rotate_seal_key(new_key_arn: str, run_by: str):
    """
    Order of operations is critical:
    1. Generate new key in HSM
    2. ROOT SIGNS the transition statement (old_key_id -> new_key_id, valid_from)
    3. Transition statement is published (portal + gazette + archive)
    4. New seals start using new key; old key retained but never used again
    5. Pubkey published
    """
    now = datetime.now(timezone.utc).isoformat()
    old_key_id = settings.SEAL_KEY_ID

    transition = {
        "tender_id": "*",  # applies globally
        "action": "seal_key_transition",
        "from_key_id": old_key_id,
        "to_key_id": new_key_arn,
        "valid_from": now,
        "reason": "scheduled_annual_rotation",
    }
    transition_bytes = json.dumps(transition, sort_keys=True,
                                  separators=(",", ":")).encode()

    # ROOT KEY signs the transition — this is the only way new seal keys
    # become trusted. The root ceremony happens here, quorum required.
    root_sig = await root_quorum_sign(transition_bytes)

    # Verify the transition before deploying
    if not verify_root_signature(root_sig, transition_bytes,
                                  await load_root_pubkey()):
        raise RuntimeError("root signature failed verification — aborting")

    # Store transition (append-only)
    async with db.transaction() as tx:
        await tx.execute("""
            INSERT INTO technical.key_transitions
              (from_key_id, to_key_id, valid_from, transition, root_sig, run_by)
            VALUES ($1, $2, $3, $4::jsonb, $5, $6)
        """, old_key_id, new_key_arn, now,
             json.dumps(transition), root_sig, run_by)
        await append_audit(tx, "*", None, run_by, "seal_key_rotation",
                           "technical.key_transitions", None, None, transition)

    # Update config (new deployment picks this up)
    await notify_operations(f"Seal key rotating from {old_key_id} to {new_key_arn}")
