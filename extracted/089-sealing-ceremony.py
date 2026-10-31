# app/sealing/ceremony.py
import hashlib, json, base64
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel

class SealChallenge(BaseModel):
    tender_id: str
    tender_reference: str
    envelope: str
    merkle_root: str
    snapshot_sha256: str
    leaf_count: int
    coverage: dict           # {unreviewed: 0, needs_clarification: 0, total: N}
    approved_by: str         # lead user id
    witnessed_by: str | None # optional second FIDO2 approver
    issued_at: str
    expires_at: str
    nonce: str

    def canonical(self) -> bytes:
        return json.dumps(self.model_dump(), sort_keys=True,
                          separators=(",", ":")).encode()

async def create_seal_challenge(
    tender_id: str, envelope: str, user_id: str
) -> SealChallenge:
    # verify coverage first — must be 100% reviewed
    cov = await db.fetchrow(f"""
        SELECT COUNT(*) FILTER (WHERE human_status IS NULL) AS unreviewed,
               COUNT(*) AS total
        FROM {envelope}.compliance_rows WHERE tender_id = $1
    """, tender_id)
    if cov["unreviewed"] != 0:
        raise HTTPException(409, f"{cov['unreviewed']} rows unreviewed; cannot seal")

    tender = await db.fetchrow(
        "SELECT reference FROM core.tenders WHERE id = $1", tender_id)
    snapshot = await build_snapshot(tender_id, envelope)
    snapshot_bytes = json.dumps(snapshot, sort_keys=True,
                                separators=(",", ":")).encode()
    leaves = [canonical_row(r) for r in _flatten_for_merkle(snapshot)]

    now = datetime.now(timezone.utc)
    return SealChallenge(
        tender_id=tender_id,
        tender_reference=tender["reference"],
        envelope=envelope,
        merkle_root=merkle_root(leaves),
        snapshot_sha256=hashlib.sha256(snapshot_bytes).hexdigest(),
        leaf_count=len(leaves),
        coverage={"unreviewed": 0, "needs_clarification": 0,
                  "total": cov["total"]},
        approved_by=user_id,
        witnessed_by=None,
        issued_at=now.isoformat(),
        expires_at=(now + timedelta(minutes=15)).isoformat(),
        nonce=base64.b16encode(os.urandom(16)).decode(),
    )

# Displayed to the signer — this is what the human actually reviews
def render_challenge(ch: SealChallenge) -> str:
    return f"""
    ┌─────────────────────────────────────────────────────────────────┐
    │  SEAL AUTHORISATION REQUEST                                     │
    ├─────────────────────────────────────────────────────────────────┤
    │  Tender:            {ch.tender_reference}
    │  Envelope:          {ch.envelope.upper()}
    │  Leaf count:        {ch.leaf_count}
    │  Coverage:          {ch.coverage['total']} rows, 0 unreviewed
    │
    │  Snapshot SHA-256:  {ch.snapshot_sha256}
    │  Merkle root:       {ch.merkle_root}
    │  Nonce:             {ch.nonce}
    │
    │  Issued:            {ch.issued_at}
    │  Expires:           {ch.expires_at}  (15 minutes)
    │  Approved by:       {ch.approved_by}
    │  Witnessed by:      {ch.witnessed_by or 'pending'}
    ├─────────────────────────────────────────────────────────────────┤
    │  Signing commits to the exact snapshot above. Any modification  │
    │  after signing will fail verification.                          │
    └─────────────────────────────────────────────────────────────────┘
    """

# The KMS call — this is where the HSM actually signs
async def sign_challenge(ch: SealChallenge) -> tuple[str, str]:
    if datetime.fromisoformat(ch.expires_at) < datetime.now(timezone.utc):
        raise HTTPException(410, "challenge expired; re-initiate")
    if not ch.witnessed_by:
        raise HTTPException(403, "witness approval required before signing")

    # AWS KMS: sign with an asymmetric Ed25519 key
    resp = await kms_client.sign(
        KeyId=settings.SEAL_KEY_ARN,
        Message=ch.canonical(),
        MessageType="RAW",
        SigningAlgorithm="ECDSA_SHA_256",  # or ED25519 if KMS supports
    )
    signature = base64.b64encode(resp["Signature"]).decode()
    key_id = resp["KeyId"]
    # KMS returns the actual key version — record it
    return signature, key_id
