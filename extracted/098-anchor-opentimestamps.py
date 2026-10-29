# anchor/opentimestamps.py
import subprocess, tempfile, os

async def anchor_to_bitcoin(manifest_bytes: bytes) -> dict:
    with tempfile.TemporaryDirectory() as d:
        manifest_path = os.path.join(d, "MANIFEST.json")
        ots_path = manifest_path + ".ots"
        with open(manifest_path, "wb") as f:
            f.write(manifest_bytes)
        # ots-cli submits the hash to calendar servers
        subprocess.run(["ots", "stamp", manifest_path], check=True, timeout=60)
        with open(ots_path, "rb") as f:
            ots_proof = f.read()
    return {
        "type": "opentimestamps",
        "proof_bytes": base64.b64encode(ots_proof).decode(),
        "status": "pending",  # becomes "confirmed" after ~1 hour (next block)
    }

def verify_ots(manifest_bytes: bytes, proof: dict) -> dict:
    with tempfile.TemporaryDirectory() as d:
        manifest_path = os.path.join(d, "MANIFEST.json")
        ots_path = manifest_path + ".ots"
        with open(manifest_path, "wb") as f:
            f.write(manifest_bytes)
        with open(ots_path, "wb") as f:
            f.write(base64.b64decode(proof["proof_bytes"]))
        result = subprocess.run(
            ["ots", "verify", manifest_path],
            capture_output=True, text=True, timeout=120)
        return {
            "ok": result.returncode == 0,
            "output": result.stdout,
        }
