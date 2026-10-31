# app/audit/verify.py
async def verify_chain(tender_id: str) -> dict:
    rows = await db.fetch("""
        SELECT id, ts, envelope, actor, action, target_table, target_id,
               before, after, prev_hash, hash
        FROM audit.ledger
        WHERE tender_id = $1
        ORDER BY ts, id
    """, tender_id)
    prev = GENESIS
    for r in rows:
        payload = {
            "tender_id": tender_id,
            "envelope": r["envelope"],
            "actor": str(r["actor"]) if r["actor"] else None,
            "action": r["action"],
            "target_table": r["target_table"],
            "target_id": str(r["target_id"]) if r["target_id"] else None,
            "before": r["before"],
            "after": r["after"],
            "prev_hash": r["prev_hash"],
        }
        expected = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"),
                       default=str).encode()
        ).hexdigest()
        if r["prev_hash"] != prev:
            return {"ok": False, "reason": "prev_hash mismatch",
                    "at": str(r["id"]), "ts": r["ts"].isoformat()}
        if expected != r["hash"]:
            return {"ok": False, "reason": "hash mismatch",
                    "at": str(r["id"]), "ts": r["ts"].isoformat()}
        prev = r["hash"]
    return {"ok": True, "entries": len(rows), "head": prev}
