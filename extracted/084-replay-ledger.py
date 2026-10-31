# tools/replay_ledger.py
"""Reconstruct audit state from exported bundle into a fresh Postgres DB."""
import gzip, json, argparse
from pathlib import Path
import psycopg

def replay(bundle_dir: Path, dsn: str):
    manifests = sorted(bundle_dir.glob("*/MANIFEST.json"))
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_witness.ledger (
                    id UUID, ts TIMESTAMPTZ, tender_id UUID, envelope TEXT,
                    actor UUID, action TEXT, target_table TEXT, target_id UUID,
                    before JSONB, after JSONB, prev_hash TEXT, hash TEXT,
                    PRIMARY KEY (hash)
                );
                CREATE INDEX IF NOT EXISTS ON audit_witness.ledger (tender_id, ts);
            """)
            # load in manifest order
            for mp in manifests:
                with gzip.open(mp.parent / "ledger.ndjson.gz", "rt") as f:
                    for line in f:
                        e = json.loads(line)
                        cur.execute("""
                            INSERT INTO audit_witness.ledger VALUES
                              (%(id)s,%(ts)s,%(tender_id)s,%(envelope)s,%(actor)s,
                               %(action)s,%(target_table)s,%(target_id)s,
                               %(before)s,%(after)s,%(prev_hash)s,%(hash)s)
                            ON CONFLICT (hash) DO NOTHING
                        """, e)
        conn.commit()
