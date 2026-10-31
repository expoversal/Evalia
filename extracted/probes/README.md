# Probes for the extracted fragments

These scripts are audit harnesses. They exercise the DeepSeek fragments in `extracted/` to show whether those fragments run and whether they behave as the transcript claims. They are not Evalia code, and they use only synthetic data.

| File | What it tests | Probe codes |
|---|---|---|
| `probe_python.py` | Pure-Python fragments: evidence verification, aggregation, BQ checks, rate outliers, deduplication, prompt templating, access policy, JWT handling, Merkle sealing, award formulas and imports of the FROST and Rekor libraries | P008 to P128 |
| `probe_ledger.py` | The audit ledger (053) and chain verifier (054) against a live PostgreSQL database | L1 to L4 |
| `probe_verifier.py` | The offline audit verifier (082) against synthetic export bundles | V1 to V5 |
| `probe_schema.sql` | Behaviour of the SQL schema (041 to 078) with test rows: seals, triggers, roles, the award function, and objects the Python expects but the SQL never creates | P1 to P15 |

## Requirements

- Python 3.12 or later, with `pydantic`, `numpy`, `cryptography`, `fastapi`, `python-jose`, `rapidfuzz`, `reportlab`, `asyncpg` and `pyyaml`
- PostgreSQL 16, for the ledger and schema probes

## Running

From the repository root, in a virtual environment:

```bash
python extracted/probes/probe_python.py
```

```bash
python -I extracted/probes/probe_verifier.py "$(mktemp -d)"
```

For the database probes, create two empty databases. Load fragments 041 and 044 into the first (for `probe_ledger.py`). Load fragments 041 to 045, 052, 072, 074 and 078 into the second, in that order, then run `probe_schema.sql` against it:

```bash
PROBE_DSN="postgresql://localhost/evalia_ledger" python extracted/probes/probe_ledger.py
```

```bash
psql -X -d evalia_audit -f extracted/probes/probe_schema.sql
```

`probe_schema.sql` creates the roles `app_role` and `sealer_role` (through fragment 045) and changes the ledger trigger. Use a throwaway cluster.

## Results recorded on 29 October 2026

The verdicts in [`../INVENTORY.md`](../INVENTORY.md) record the results. In summary:

- **P008c.** A genuine quote from the first of two chunks of the same document is rejected.
- **P021b.** The S$10 million and S$1 million turnover requirements merge into one record.
- **P019 to P024.** Every prompt raises KeyError under `str.format()`.
- **P055.** The matrix endpoint returns 403 to every role.
- **P073a.** Tied bids are ranked 1 and 2.
- **P128.** `frost_ceremony.py` cannot be imported.
- **L2.** Any ledger entry with a payload fails verification.
- **L3.** Overlapping transactions break the chain.
- **L4.** A timestamp edit goes undetected.
- **V2 and V5.** The offline verifier passes a backdated entry and a truncated bundle.
- **V4.** The verifier fails every multi-day bundle in the layout that fragment 080 writes.
- **P4.** The award function passes a bidder that failed a mandatory requirement and returns a NULL price for every bidder.
- **P5.** The application role revokes a seal without co-signature.
- **P7.** A superuser truncates the "append-only" ledger.
