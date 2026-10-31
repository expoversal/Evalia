# app/sealing/unseal_ceremony.py
# Using the `frost-ed25519` library (Rust-backed, mature)
from frost_ed25519 import (
    KeyGenCeremony, SigningCeremony,
    TrustedDealerKeygen, KeyPackage, PublicKeyPackage,
)
import base64, os

# ── One-time setup (in a physical ceremony, witnessed + notarised) ──────────
def provision_unseal_quorum(participants: list[dict], threshold: int):
    """
    participants: [{name, role, email, yubikey_serial}]
    threshold: e.g. 3 for 3-of-5
    """
    # Trusted-dealer keygen: generates the group key + each share
    # In the highest-security setup, use DKG (Distributed Key Generation)
    # instead so no single machine ever sees the full key
    kp = TrustedDealerKeygen.generate(threshold=threshold,
                                       max_signers=len(participants))
    group_pub = kp.public_key_package.group_public_key

    shares = []
    for i, p in enumerate(participants):
        share = kp.key_packages[i]
        # Encrypt share to the executive's YubiKey PIV slot
        encrypted = encrypt_to_yubikey(share, p["yubikey_serial"])
        shares.append({
            "participant_id": i + 1,
            "name": p["name"],
            "encrypted_share": encrypted,
        })
        # Physically mail the YubiKey to the executive; store the share
        # nowhere in the live system
    return {
        "group_public_key": base64.b64encode(group_pub.to_bytes()).decode(),
        "threshold": threshold,
        "max_signers": len(participants),
        "participants": shares,
        "ceremony_witnesses": [],  # filled in by ceremony
    }

# ── Unseal ceremony (each executive on their own laptop, air-gapped) ─────────
def executive_contribute(share_file: str, yubikey_pin: str,
                         unseal_challenge: bytes) -> dict:
    """Run by each executive independently. Produces one signing fragment."""
    share = decrypt_from_yubikey(share_file, yubikey_pin)
    signing_ceremony = SigningCeremony(
        message=unseal_challenge,
        key_package=share,
        # coordinator sends commitments from other participants
        signer_commitments=[],  # populated by coordinator
    )
    commitment = signing_ceremony.commit()
    return {"participant_id": share.identifier, "commitment": commitment}

def coordinator_finalize(fragments: list[dict], unseal_challenge: bytes,
                         group_pub, threshold: int) -> bytes:
    """Run by the coordinator after collecting >= threshold fragments."""
    if len(fragments) < threshold:
        raise RuntimeError(f"need {threshold} fragments, got {len(fragments)}")
    sig = SigningCeremony.aggregate(
        message=unseal_challenge,
        signer_commitments=fragments,
        public_key_package=group_pub,
    )
    # verify against the group pubkey before returning
    if not verify_signature(sig, unseal_challenge, group_pub):
        raise RuntimeError("threshold signature failed verification")
    return sig

# ── The unseal authorisation itself ─────────────────────────────────────────
def build_unseal_authorisation(
    tender_id: str, envelope: str, reason: str,
    requesting_lead: str, procurement_officer: str,
    participants_who_signed: list[int],
    fragments: list[dict], group_pub, threshold: int,
) -> dict:
    auth = {
        "action": "unseal",
        "tender_id": tender_id,
        "envelope": envelope,
        "reason": reason,
        "requesting_lead": requesting_lead,
        "procurement_officer": procurement_officer,
        "signers": participants_who_signed,
        "threshold": threshold,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    auth_bytes = json.dumps(auth, sort_keys=True,
                            separators=(",", ":")).encode()
    signature = coordinator_finalize(fragments, auth_bytes, group_pub, threshold)
    return {**auth, "signature": base64.b64encode(signature).decode(),
            "signer_key_id": "unseal-quorum-v1"}
