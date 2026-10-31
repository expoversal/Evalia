import hashlib
import json
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import base64

def _h(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def canonical(row) -> bytes:
    return json.dumps(row, sort_keys=True, separators=(",", ":")).encode()

def merkle_root(leaves: list[bytes]) -> str:
    if not leaves:
        return _h(b"")
    layer = [_h(l) for l in leaves]
    while len(layer) > 1:
        nxt = []
        for i in range(0, len(layer), 2):
            a = layer[i]
            b = layer[i+1] if i+1 < len(layer) else a
            nxt.append(_h((a+b).encode()))
        layer = nxt
    return layer[0]

@dataclass
class Seal:
    tender_id: str
    envelope: str
    merkle_root: str
    leaf_count: int
    signature: str
    signed_at: str

def seal_envelope(rows: list[dict], tender_id: str, envelope: str,
                  signer: Ed25519PrivateKey) -> Seal:
    leaves = [canonical({k: r[k] for k in sorted(r) if r[k] is not None})
              for r in rows]
    root = merkle_root(leaves)
    payload = f"{tender_id}|{envelope}|{root}|{len(leaves)}".encode()
    sig = signer.sign(payload)
    return Seal(
        tender_id=tender_id,
        envelope=envelope,
        merkle_root=root,
        leaf_count=len(leaves),
        signature=base64.b64encode(sig).decode(),
        signed_at=_utcnow_iso(),
    )
