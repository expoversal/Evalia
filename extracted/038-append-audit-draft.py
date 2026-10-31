async def append_audit(tx, tender_id, envelope, actor, action,
                       target_table, target_id, before, after):
    prev = await tx.fetchval("""
        SELECT hash FROM audit.ledger
        WHERE tender_id = $1 ORDER BY ts DESC, id DESC LIMIT 1
    """, tender_id)
    payload = {
        "tender_id": str(tender_id),
        "envelope": envelope,
        "actor": str(actor),
        "action": action,
        "target_table": target_table,
        "target_id": str(target_id),
        "before": before,
        "after": after,
        "prev_hash": prev or "0"*64,
    }
    h = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    await tx.execute("""
        INSERT INTO audit.ledger(tender_id, envelope, actor, action,
                                 target_table, target_id, before, after,
                                 prev_hash, hash)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
    """, tender_id, envelope, actor, action, target_table, target_id,
         before, after, prev or "0"*64, h)
