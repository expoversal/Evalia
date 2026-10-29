"""Build synthetic audit bundles in the layout of fragment 080 and run fragment 082 on them."""
import json, gzip, hashlib, base64, uuid, shutil, subprocess, sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
S = Path(sys.argv[1]); V = str(Path(__file__).resolve().parent.parent / '082-verify-audit.py')
key = Ed25519PrivateKey.generate()
(S/'seal.pub.pem').write_bytes(key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
T = str(uuid.uuid4())
def entry_hash(e):   # identical payload to fragment 053
    p = {k: e.get(k) for k in ['tender_id','envelope','actor','action','target_table','target_id','before','after','prev_hash']}
    return hashlib.sha256(json.dumps(p, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
def mroot(h):
    if not h: return hashlib.sha256(b"").hexdigest()
    while len(h) > 1:
        h = [hashlib.sha256((h[i] + (h[i+1] if i+1 < len(h) else h[i])).encode()).hexdigest() for i in range(0, len(h), 2)]
    return h[0]
def build(root, days=2, chain_manifests=True):
    shutil.rmtree(root, ignore_errors=True); prev, prev_sha = "0"*64, None
    t0 = datetime(2026, 4, 1, 9, tzinfo=timezone.utc)
    for d in range(days):
        out = root/f"2026-04-0{d+1}"; out.mkdir(parents=True)
        rows = []
        for i in range(3):
            e = dict(id=str(uuid.uuid4()), ts=(t0 + timedelta(days=d, hours=i)).isoformat(), tender_id=T, envelope='technical',
                     actor=None, action='view', target_table=None, target_id=None, before=None, after=None, prev_hash=prev)
            e['hash'] = entry_hash(e); prev = e['hash']; rows.append(e)
        with gzip.GzipFile(out/'ledger.ndjson.gz', 'wb', mtime=0) as f:
            for e in rows: f.write((json.dumps(e, sort_keys=True, separators=(",", ":")) + "\n").encode())
        (out/'seals.json').write_text('[]')
        m = dict(version=1, tender_id=T, period={'from': rows[0]['ts'], 'to': rows[-1]['ts']}, entry_count=len(rows),
                 first_entry_hash=rows[0]['hash'], last_entry_hash=rows[-1]['hash'], first_entry_prev_hash=rows[0]['prev_hash'],
                 merkle_root=mroot([e['hash'] for e in rows]), checkpoint=None, seal_merkle_roots=[],
                 previous_manifest_sha256=prev_sha if chain_manifests else None, exported_at=rows[-1]['ts'])
        m['signature'] = base64.b64encode(key.sign(json.dumps(m, sort_keys=True, separators=(",", ":")).encode())).decode()
        m['signer_key_id'] = 'k1'
        (out/'MANIFEST.json').write_text(json.dumps(m, sort_keys=True, indent=2))
        prev_sha = hashlib.sha256((out/'MANIFEST.json').read_bytes()).hexdigest()
def edit(root, day, idx, field, value):
    p = root/day/'ledger.ndjson.gz'
    lines = gzip.open(p, 'rt').read().splitlines(); e = json.loads(lines[idx]); e[field] = value
    lines[idx] = json.dumps(e, sort_keys=True, separators=(",", ":"))
    with gzip.GzipFile(p, 'wb', mtime=0) as f: f.write(("\n".join(lines) + "\n").encode())
def run(tag, root):
    r = subprocess.run([sys.executable, V, '--bundle', str(root), '--pubkey', str(S/'seal.pub.pem'), '--format', 'json'], capture_output=True, text=True)
    out = json.loads(r.stdout); print(f"{tag:58} -> {'PASS' if out['ok'] else 'FAIL'} {out['errors'][:1]}")
B = S/'bundle'
build(B); run('V1 two days, manifests chained correctly', B)
build(B); edit(B, '2026-04-01', 1, 'ts', '2026-03-01T00:00:00+00:00'); run('V2 entry timestamp moved back 31 days', B)
build(B); edit(B, '2026-04-01', 1, 'action', 'override'); run('V3 entry action changed', B)
build(B, chain_manifests=False); run('V4 manifests as fragment 080 writes them (prev = None)', B)
build(B); shutil.rmtree(B/'2026-04-02'); run('V5 most recent day deleted from bundle', B)
