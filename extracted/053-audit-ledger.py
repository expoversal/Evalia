# app/audit/ledger.py
import hashlib, json

GENESIS = "0" * 64

async def append_audit(tx, tender_id, envelope, actor,
                       action, target_table, target_id,
                       before, after):
    prev = await tx.fetchval("""
        SELECT hash FROM audit.ledger
        WHERE tender_id = $1
        ORDER BY ts DESC, id DESC LIMIT 1
    """, tender_id) or GENESIS

    payload = {
        "tender_id": str(tender_id),
        "envelope": envelope,
        "actor": str(actor) if actor else None,
        "action": action,
        "target_table": target_table,
        "target_id": str(target_id) if target_id else None,
        "before": before,
        "after": after,
        "prev_hash": prev,
    }
    h = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"),
                   default=str).encode()
    ).hexdigest()
    await tx.execute("""
        INSERT INTO audit.ledger
          (tender_id, envelope, actor, action, target_table, target_id,
           before, after, prev_hash, hash)
        VALUES ($1,$2,$3,$4,$5,$6,$7::jsonb,$8::jsonb,$9,$10)
    """, tender_id, envelope, actor, action, target_table, target_id,
         json.dumps(before, default=str) if before else None,
         json.dumps(after, default=str) if after else None,
         prev, h)
    return h
