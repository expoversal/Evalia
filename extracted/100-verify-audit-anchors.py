# tools/verify_audit.py — additions
from anchor.rfc3161 import verify_timestamp
from anchor.rekor import verify_rekor_inclusion
from anchor.opentimestamps import verify_ots

def verify_anchors(manifest_path: Path, manifest_bytes: bytes,
                   res: VerifyResult):
    # RFC 3161
    tsr_path = manifest_path.with_suffix(".tsr")
    if not tsr_path.exists():
        res.fail(f"missing {tsr_path.name}")
    else:
        tsr = {"type": "rfc3161",
               "token_der": base64.b64encode(tsr_path.read_bytes()).decode()}
        v = verify_timestamp(manifest_bytes, tsr)
        if not v["ok"]:
            res.fail(f"RFC 3161 verification failed: {v['reason']}")
        else:
            res.stats["timestamp"] = v["timestamp"]

    # Rekor
    rekor_path = manifest_path.with_suffix(".rekor.json")
    if not rekor_path.exists():
        res.warn(f"no Rekor anchor for {manifest_path.parent.name}")
    else:
        v = verify_rekor_inclusion(manifest_bytes, json.loads(rekor_path.read_text()))
        if not v["ok"]:
            res.fail(f"Rekor inclusion verification failed")
        else:
            res.stats["rekor_index"] = v.get("log_index")

    # OpenTimestamps
    ots_path = manifest_path.with_suffix(".ots")
    if not ots_path.exists():
        res.warn(f"no Bitcoin anchor for {manifest_path.parent.name}")
    else:
        v = verify_ots(manifest_bytes, {"proof_bytes": base64.b64encode(
            ots_path.read_bytes()).decode()})
        if not v["ok"]:
            res.fail(f"OpenTimestamps verification failed: {v['output']}")
