#!/usr/bin/env python3
# tools/verify_audit.py
"""Offline audit verifier.

Usage:
    verify_audit.py --bundle /path/to/audit/<tender>/ --pubkey seal.pub.pem
                    [--format text|json]

Bundle layout:
    audit/<tender>/
        2026-04-01/
            ledger.ndjson.gz
            seals.json
            MANIFEST.json
        2026-04-02/
            ...
"""
import argparse, base64, gzip, hashlib, json, sys
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

GENESIS = "0" * 64

@dataclass
class VerifyResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def fail(self, msg: str):
        self.ok = False
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)

def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def canonical_manifest_bytes(manifest: dict) -> bytes:
    m = {k: v for k, v in manifest.items() if k not in ("signature", "signer_key_id")}
    return json.dumps(m, sort_keys=True, separators=(",", ":")).encode()

def verify_manifest_signature(manifest: dict, pubkey: Ed25519PublicKey, res: VerifyResult):
    if "signature" not in manifest:
        res.fail("manifest missing signature")
        return
    try:
        pubkey.verify(base64.b64decode(manifest["signature"]),
                      canonical_manifest_bytes(manifest))
    except Exception as e:
        res.fail(f"manifest signature invalid: {e}")

def recompute_entry_hash(entry: dict) -> str:
    payload = {
        "tender_id": entry["tender_id"],
        "envelope": entry.get("envelope"),
        "actor": entry.get("actor"),
        "action": entry["action"],
        "target_table": entry.get("target_table"),
        "target_id": entry.get("target_id"),
        "before": entry.get("before"),
        "after": entry.get("after"),
        "prev_hash": entry["prev_hash"],
    }
    return sha256(json.dumps(payload, sort_keys=True,
                             separators=(",", ":"),
                             default=str).encode())

def merkle_root(hashes: list[str]) -> str:
    if not hashes: return sha256(b"")
    layer = list(hashes)
    while len(layer) > 1:
        nxt = [sha256((layer[i] + layer[i+1] if i+1 < len(layer) else layer[i]+layer[i]).encode())
               for i in range(0, len(layer), 2)]
        layer = nxt
    return layer[0]

def verify_chain(entries: list[dict], expected_first_prev: str, res: VerifyResult):
    prev = expected_first_prev
    for i, e in enumerate(entries):
        if e["prev_hash"] != prev:
            res.fail(f"entry {i} ({e['id']}): prev_hash mismatch "
                     f"(expected {prev[:12]}…, got {e['prev_hash'][:12]}…)")
            return
        if recompute_entry_hash(e) != e["hash"]:
            res.fail(f"entry {i} ({e['id']}): recomputed hash mismatch")
            return
        prev = e["hash"]

def verify_manifest(manifest_path: Path, pubkey: Ed25519PublicKey,
                    res: VerifyResult) -> dict | None:
    manifest = json.loads(manifest_path.read_text())
    verify_manifest_signature(manifest, pubkey, res)
    if not res.ok:
        return None

    # ledger
    ndjson_path = manifest_path.parent / "ledger.ndjson.gz"
    entries = []
    with gzip.open(ndjson_path, "rt", encoding="utf-8") as f:
        for line in f:
            entries.append(json.loads(line))

    if len(entries) != manifest["entry_count"]:
        res.fail(f"entry_count mismatch: manifest={manifest['entry_count']}, "
                 f"file={len(entries)}")
    if entries[0]["hash"] != manifest["first_entry_hash"]:
        res.fail("first_entry_hash mismatch")
    if entries[-1]["hash"] != manifest["last_entry_hash"]:
        res.fail("last_entry_hash mismatch")
    if entries[0]["prev_hash"] != manifest["first_entry_prev_hash"]:
        res.fail("first_entry_prev_hash mismatch")

    verify_chain(entries, manifest["first_entry_prev_hash"], res)

    root = merkle_root([e["hash"] for e in entries])
    if root != manifest["merkle_root"]:
        res.fail(f"merkle_root mismatch: recomputed {root[:12]}…, "
                 f"manifest {manifest['merkle_root'][:12]}…")

    # seals
    seals = json.loads((manifest_path.parent / "seals.json").read_text())
    for s_meta in manifest["seal_merkle_roots"]:
        matching = [s for s in seals
                    if s["envelope"] == s_meta["envelope"]
                    and s["merkle_root"] == s_meta["merkle_root"]]
        if not matching:
            res.fail(f"seal {s_meta['envelope']}: no matching seal record")
            continue
        # verify the seal signature itself
        try:
            msg = (f"{matching[0]['tender_id']}|{matching[0]['envelope']}|"
                   f"{matching[0]['merkle_root']}|{matching[0]['leaf_count']}|"
                   f"{matching[0]['prev_seal_id'] or ''}").encode()
            pubkey.verify(base64.b64decode(matching[0]["signature"]), msg)
        except Exception as e:
            res.fail(f"seal {s_meta['envelope']}: signature invalid: {e}")

    return manifest

def verify_bundle(bundle_dir: Path, pubkey: Ed25519PublicKey,
                  res: VerifyResult) -> None:
    manifests = sorted(bundle_dir.glob("*/MANIFEST.json"))
    if not manifests:
        res.fail(f"no MANIFEST.json found under {bundle_dir}")
        return

    prev_sha = None
    for mp in manifests:
        m = verify_manifest(mp, pubkey, res)
        if m is None:
            res.fail(f"{mp.parent.name}: manifest verification failed, stopping")
            return
        if m.get("previous_manifest_sha256") != prev_sha:
            res.fail(f"{mp.parent.name}: previous_manifest_sha256 mismatch "
                     f"(expected {prev_sha}, got {m.get('previous_manifest_sha256')})")
            return
        prev_sha = sha256(mp.read_bytes())

    res.stats["manifests"] = len(manifests)
    res.stats["last_manifest_sha"] = prev_sha

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True, type=Path)
    ap.add_argument("--pubkey", required=True, type=Path)
    ap.add_argument("--format", choices=["text", "json"], default="text")
    args = ap.parse_args()

    pub = serialization.load_pem_public_key(args.pubkey.read_bytes())
    if not isinstance(pub, Ed25519PublicKey):
        print("public key must be Ed25519", file=sys.stderr)
        sys.exit(2)

    res = VerifyResult()
    verify_bundle(args.bundle, pub, res)

    if args.format == "json":
        print(json.dumps({"ok": res.ok, "errors": res.errors,
                          "warnings": res.warnings, "stats": res.stats},
                         indent=2))
    else:
        print(f"Bundle: {args.bundle}")
        print(f"Result: {'PASS' if res.ok else 'FAIL'}")
        for k, v in res.stats.items():
            print(f"  {k}: {v}")
        for e in res.errors:
            print(f"  ERROR: {e}")
        for w in res.warnings:
            print(f"  WARN:  {w}")

    sys.exit(0 if res.ok else 1)

if __name__ == "__main__":
    main()
