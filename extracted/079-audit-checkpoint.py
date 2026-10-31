# audit/checkpoint.py — runs as a CronJob every hour
async def create_checkpoint(tender_id: str):
    head = await db.fetchrow("""
        SELECT id, hash, (SELECT COUNT(*) FROM audit.ledger WHERE tender_id = $1)
               AS n
        FROM audit.ledger
        WHERE tender_id = $1
        ORDER BY ts DESC, id DESC LIMIT 1
    """, tender_id)
    if not head:
        return None
    prev = await db.fetchval("""
        SELECT id FROM audit.checkpoints WHERE tender_id = $1
        ORDER BY created_at DESC LIMIT 1
    """, tender_id)
    now = datetime.now(timezone.utc).isoformat()
    message = f"{tender_id}|{head['hash']}|{head['n']}|{now}".encode()
    sig = await kms.sign(settings.SEAL_KEY_ID, message)
    return await db.fetchval("""
        INSERT INTO audit.checkpoints
          (tender_id, head_id, head_hash, entry_count,
           signature, signer_key_id, prev_checkpoint_id, created_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
        RETURNING id
    """, tender_id, head["id"], head["hash"], head["n"],
         base64.b64encode(sig).decode(), settings.SEAL_KEY_ID, prev, now)
