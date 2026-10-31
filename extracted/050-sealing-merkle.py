# app/sealing/merkle.py
import hashlib, json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)
import base64

def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def canonical_row(row: dict) -> bytes:
    """Deterministic JSON: sorted keys, no whitespace, no None."""
    clean = {k: v for k, v in sorted(row.items()) if v is not None}
    return json.dumps(clean, sort_keys=True, separators=(",", ":"),
                      default=str).encode()

def merkle_root(leaves: list[bytes]) -> str:
    if not leaves:
        return _sha(b"")
    layer = [_sha(l) for l in leaves]
    while len(layer) > 1:
        nxt = []
        for i in range(0, len(layer), 2):
            a = layer[i]
            b = layer[i+1] if i + 1 < len(layer) else a
            nxt.append(_sha((a + b).encode()))
        layer = nxt
    return layer[0]

@dataclass
class SealedPayload:
    tender_id: str
    envelope: str
    merkle_root: str
    leaf_count: int
    prev_seal_id: str | None
    signed_at: str
    signature: str
    signer_key_id: str

def sign_seal(rows: list[dict], tender_id: str, envelope: str,
              prev_seal_id: str | None, signer_key_id: str,
              key: Ed25519PrivateKey) -> SealedPayload:
    leaves = [canonical_row(r) for r in rows]
    root = merkle_root(leaves)
    signed_at = datetime.now(timezone.utc).isoformat()
    message = f"{tender_id}|{envelope}|{root}|{len(leaves)}|{prev_seal_id or ''}".encode()
    sig = key.sign(message)
    return SealedPayload(
        tender_id=tender_id, envelope=envelope,
        merkle_root=root, leaf_count=len(leaves),
        prev_seal_id=prev_seal_id, signed_at=signed_at,
        signature=base64.b64encode(sig).decode(),
        signer_key_id=signer_key_id,
    )

def verify_seal(payload: SealedPayload, snapshot: list[dict],
                pubkey: Ed25519PublicKey) -> bool:
    leaves = [canonical_row(r) for r in snapshot]
    if merkle_root(leaves) != payload.merkle_root:
        return False
    message = (f"{payload.tender_id}|{payload.envelope}|{payload.merkle_root}|"
               f"{payload.leaf_count}|{payload.prev_seal_id or ''}").encode()
    try:
        pubkey.verify(base64.b64decode(payload.signature), message)
        return True
    except Exception:
        return False
