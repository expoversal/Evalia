# anchor/rfc3161.py
from rfc3161ng import RemoteTimestamper
import hashlib

async def timestamp_manifest(manifest_bytes: bytes) -> dict:
    """Returns an RFC 3161 timestamp token for the manifest."""
    tsr = RemoteTimestamper(
        "https://freetsa.org/tsr",       # or a paid TSA for higher assurance
        hashname="sha256",
        certificate=None,                # or your TSA's cert
    ).timestamp(manifest_bytes, include_tsa_certificate=True)
    return {
        "type": "rfc3161",
        "provider": "freetsa.org",
        "hash": hashlib.sha256(manifest_bytes).hexdigest(),
        "token_der": base64.b64encode(tsr).decode(),
        # Include the TSA's current certificate chain for offline verification
        "tsa_certs": [base64.b64encode(c).decode() for c in tsr.tsa_certs],
    }
