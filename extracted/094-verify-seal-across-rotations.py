async def verify_seal_across_rotations(seal: dict) -> bool:
    # 1. Load the pubkey for the key that signed this seal
    pub = await load_archived_pubkey(seal["signer_key_id"])
    if pub is None:
        return False
    # 2. Verify the seal's signature
    if not verify_seal_signature(seal, pub):
        return False
    # 3. Verify the key was valid at the seal's signed_at
    transition = await db.fetchrow("""
        SELECT * FROM technical.key_transitions
        WHERE to_key_id = $1 AND valid_from <= $2
        ORDER BY valid_from DESC LIMIT 1
    """, seal["signer_key_id"], seal["signed_at"])
    if transition and not verify_root_signature(
        transition["root_sig"], transition["transition"].encode(),
        await load_root_pubkey()):
        return False
    # 4. If signer_key_id is the current key, no transition needed
    return True
