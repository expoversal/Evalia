# audit/export.py — runs as a CronJob nightly at 02:00 UTC
import gzip, json, hashlib
from pathlib import Path

def merkle_root_over_hashes(hashes: list[str]) -> str:
    if not hashes: return hashlib.sha256(b"").hexdigest()
    layer = hashes
    while len(layer) > 1:
        nxt = []
        for i in range(0, len(layer), 2):
            a = layer[i]
            b = layer[i+1] if i+1 < len(layer) else a
            nxt.append(hashlib.sha256((a+b).encode()).hexdigest())
        layer = nxt
    return layer[0]

async def export_tender(tender_id: str, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Entries since the last export
    last = await db.fetchrow("""
        SELECT max(created_at) FROM audit.exports WHERE tender_id = $1
    """, tender_id)
    since = last["max"] if last and last["max"] else "1970-01-01"

    rows = await db.fetch("""
        SELECT id::text, ts, tender_id::text, envelope, actor::text,
               action, target_table, target_id::text,
               before, after, prev_hash, hash
        FROM audit.ledger
        WHERE tender_id = $1 AND ts > $2
        ORDER BY ts, id
    """, tender_id, since)

    if not rows:
        return None

    # 2. Write NDJSON (gzipped, deterministic)
    ndjson_path = out_dir / "ledger.ndjson.gz"
    with gzip.open(ndjson_path, "wt", encoding="utf-8", mtime=0) as f:
        for r in rows:
            entry = {k: (r[k].isoformat() if hasattr(r[k], "isoformat") else r[k])
                     for k in r.keys()}
            f.write(json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n")

    # 3. Merkle root over entry hashes (the entries carry their own prev_hash chain)
    root = merkle_root_over_hashes([r["hash"] for r in rows])

    # 4. Seal snapshots (publicly verifiable)
    seals = await db.fetch("""
        SELECT tender_id::text, envelope, merkle_root, leaf_count, snapshot,
               signature, signer_key_id, signed_at::text, prev_seal_id::text,
               revoked_at::text, revoke_reason
        FROM technical.seals WHERE tender_id = $1
        UNION ALL
        SELECT tender_id::text, envelope, merkle_root, leaf_count, snapshot,
               signature, signer_key_id, signed_at::text, prev_seal_id::text,
               revoked_at::text, revoke_reason
        FROM commercial.seals WHERE tender_id = $1
        ORDER BY signed_at
    """, tender_id)
    seals_path = out_dir / "seals.json"
    seals_path.write_text(json.dumps(
        [dict(r) for r in seals], sort_keys=True, indent=2, default=str))

    # 5. Checkpoint covering this export
    ckpt = await db.fetchrow("""
        SELECT id::text, created_at::text, head_id::text, head_hash,
               entry_count, signature, signer_key_id, prev_checkpoint_id::text
        FROM audit.checkpoints WHERE tender_id = $1
        ORDER BY created_at DESC LIMIT 1
    """, tender_id)

    # 6. Manifest — signed, chained to previous manifest
    prev_manifest_path = out_dir.parent / "MANIFEST.json"
    prev_manifest_sha = None
    if prev_manifest_path.exists():
        prev_manifest_sha = hashlib.sha256(prev_manifest_path.read_bytes()).hexdigest()

    manifest = {
        "version": 1,
        "tender_id": tender_id,
        "period": {
            "from": rows[0]["ts"].isoformat(),
            "to": rows[-1]["ts"].isoformat(),
        },
        "entry_count": len(rows),
        "first_entry_hash": rows[0]["hash"],
        "last_entry_hash": rows[-1]["hash"],
        "first_entry_prev_hash": rows[0]["prev_hash"],
        "merkle_root": root,
        "checkpoint": dict(ckpt) if ckpt else None,
        "seal_merkle_roots": [
            {"envelope": s["envelope"], "merkle_root": s["merkle_root"],
             "leaf_count": s["leaf_count"], "signature": s["signature"],
             "signer_key_id": s["signer_key_id"]}
            for s in seals
        ],
        "previous_manifest_sha256": prev_manifest_sha,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }

    # 7. Sign the manifest with the KMS
    manifest_bytes = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    manifest_sig = await kms.sign(settings.SEAL_KEY_ID, manifest_bytes)
    manifest["signature"] = base64.b64encode(manifest_sig).decode()
    manifest["signer_key_id"] = settings.SEAL_KEY_ID

    manifest_path.write_text(json.dumps(manifest, sort_keys=True, indent=2))
    manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    # 8. Upload to WORM bucket (Object Lock, COMPLIANCE mode, 7-year retention)
    prefix = f"audit/{tender_id}/{rows[-1]['ts'].date().isoformat()}"
    for local, name in [(ndjson_path, "ledger.ndjson.gz"),
                        (seals_path, "seals.json"),
                        (manifest_path, "MANIFEST.json")]:
        await s3.put_object(
            Bucket=settings.WORM_BUCKET,
            Key=f"{prefix}/{name}",
            Body=local.read_bytes(),
            ObjectLockMode="COMPLIANCE",
            ObjectLockRetainUntilDate=datetime.now(timezone.utc) + timedelta(days=365*7),
            ChecksumAlgorithm="SHA256",
        )

    # 9. Record the export in the live DB (for incremental since-last-export)
    async with db.transaction() as tx:
        await tx.execute("""
            INSERT INTO audit.exports
              (tender_id, period_to, entry_count, merkle_root, manifest_sha,
               s3_prefix, signature)
            VALUES ($1,$2,$3,$4,$5,$6,$7)
        """, tender_id, rows[-1]["ts"], len(rows), root, manifest_sha,
             prefix, manifest["signature"])

    # 10. Publish the manifest hash to the external anchor (see B.7)
    await anchor.publish(tender_id, manifest_sha, manifest["merkle_root"])

    return {"prefix": prefix, "manifest_sha": manifest_sha}
