# anchor/rekor.py
import requests, hashlib, base64

async def anchor_to_rekor(manifest_bytes: bytes, manifest: dict) -> dict:
    """Submit the manifest hash to the public Sigstore Rekor log."""
    digest = hashlib.sha256(manifest_bytes).hexdigest()

    # Construct a Rekor entry — a "hashedrekord" of type sha256
    entry = {
        "apiVersion": "0.0.1",
        "kind": "hashedrekord",
        "spec": {
            "data": {"hash": {"algorithm": "sha256", "value": digest}},
            "signature": {
                "content": base64.b64encode(
                    (await kms.sign(settings.ANCHOR_KEY_ID,
                                    manifest_bytes))).decode(),
                "publicKey": {"content": base64.b64encode(
                    (await kms.get_public_key(settings.ANCHOR_KEY_ID))
                    .public_bytes_pem()).decode()},
            },
        },
    }
    r = requests.post("https://rekor.sigstore.dev/api/v1/log/entries",
                      json=entry, timeout=30)
    r.raise_for_status()
    resp = r.json()
    entry_uuid = next(iter(resp.keys()))
    log_index = resp[entry_uuid]["logIndex"]
    inclusion_proof = resp[entry_uuid]["verification"]["inclusionProof"]

    return {
        "type": "rekor",
        "log_url": "https://rekor.sigstore.dev",
        "entry_uuid": entry_uuid,
        "log_index": log_index,
        "inclusion_proof": inclusion_proof,
    }

def verify_rekor_inclusion(manifest_bytes: bytes, proof: dict) -> dict:
    """
    Verify the manifest is included in the Rekor log.
    Uses the log's signed tree head + inclusion proof — offline, no network call.
    """
    from sigstore_rekor_verify import verify_inclusion
    result = verify_inclusion(
        entry_uuid=proof["entry_uuid"],
        log_index=proof["log_index"],
        inclusion_proof=proof["inclusion_proof"],
        log_pubkey_pem=proof["log_public_key"],
    )
    return {
        "ok": result.valid,
        "signed_entry_timestamp": result.signed_entry_timestamp,
    }
