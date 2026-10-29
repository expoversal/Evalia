# ops/weekly/reverify_seals.py — cron, Monday 10:00 SGT
async def reverify_recent_seals(days=30):
    seals = await db.fetch("""
        SELECT s.id, s.tender_id, s.envelope, s.merkle_root, s.leaf_count,
               s.snapshot, s.signature, s.signer_key_id, s.signed_at,
               s.prev_seal_id
        FROM technical.seals s
        WHERE s.signed_at > now() - interval '%s days'
          AND s.revoked_at IS NULL
        UNION ALL
        SELECT s.id, s.tender_id, s.envelope, s.merkle_root, s.leaf_count,
               s.snapshot, s.signature, s.signer_key_id, s.signed_at,
               s.prev_seal_id
        FROM commercial.seals s
        WHERE s.signed_at > now() - interval '%s days'
          AND s.revoked_at IS NULL
    """ % (days, days))
    failures = []
    for seal in seals:
        pub = await load_archived_pubkey(seal["signer_key_id"])
        snapshot = seal["snapshot"]
        leaves = [canonical_row(r) for r in _flatten_for_merkle(snapshot)]
        if merkle_root(leaves) != seal["merkle_root"]:
            failures.append((seal["id"], "merkle mismatch"))
            continue
        msg = f"{seal['tender_id']}|{seal['envelope']}|{seal['merkle_root']}|" \
              f"{seal['leaf_count']}|{seal['prev_seal_id'] or ''}".encode()
        try:
            pub.verify(base64.b64decode(seal["signature"]), msg)
        except Exception as e:
            failures.append((seal["id"], f"signature: {e}"))
    if failures:
        await escalate_p1("seal re-verification failures", failures)
    return {"checked": len(seals), "failed": len(failures)}
