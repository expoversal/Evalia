# award/service.py
import json, hashlib
from datetime import datetime, timezone
from decimal import Decimal

def _jsonable(obj):
    if isinstance(obj, Decimal):  return str(obj)
    if isinstance(obj, datetime): return obj.isoformat()
    raise TypeError

async def compute_award(db_award, db_live, tender_id: str, actor_id: str) -> dict:
    """Runs as award_role. Reads only via award.read_after_both_sealed."""
    # 1. Pull both envelopes (only succeeds if both are sealed)
    rows = await db_award.fetch(
        "SELECT * FROM award.read_after_both_sealed($1)", tender_id)
    if not rows:
        raise RuntimeError("no bidders found")

    # 2. Pull config
    cfg = await db_live.fetchrow(
        "SELECT formula, params, frozen_at FROM award.config WHERE tender_id = $1",
        tender_id)
    if not cfg:
        raise RuntimeError(f"award.config missing for tender {tender_id}")
    if not cfg["frozen_at"]:
        raise RuntimeError("award.config not frozen — cannot compute award")

    # 3. Compute
    packages = [dict(r) for r in rows]
    formula = FORMULAS[cfg["formula"]]
    results = formula(packages, cfg["params"] or {})

    # 4. Sort and identify winner(s) — ties are a legal question, flag them
    eligible = [r for r in results if r.rank is not None]
    eligible.sort(key=lambda r: r.rank)
    winners = [r for r in eligible if r.rank == 1]

    # 5. Build the report
    report = {
        "tender_id": tender_id,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "actor": actor_id,
        "formula": cfg["formula"],
        "params": cfg["params"],
        "bidders": [
            {
                "bidder_id": r.bidder_id,
                "bidder_name": r.bidder_name,
                "passed_gates": r.passed_gates,
                "ineligible_reason": r.ineligible_reason,
                "compliance_summary": r.compliance_summary,
                "technical_score": str(r.technical_score),
                "evaluated_price": str(r.evaluated_price) if r.evaluated_price else None,
                "fee_score": str(r.fee_score) if r.fee_score else None,
                "final_score": str(r.final_score) if r.final_score else None,
                "rank": r.rank,
            }
            for r in results
        ],
        "winners": [w.bidder_id for w in winners],
        "tie": len(winners) > 1,
        "unranked": [r.bidder_id for r in results if r.rank is None],
    }

    # 6. Hash and persist
    report_bytes = json.dumps(report, sort_keys=True, separators=(",", ":")).encode()
    report_hash = hashlib.sha256(report_bytes).hexdigest()

    async with db_award.transaction() as tx:
        run_id = await tx.fetchval("""
            INSERT INTO award.runs
              (tender_id, formula, params, report, report_hash, actor)
            VALUES ($1,$2,$3::jsonb,$4::jsonb,$5,$6)
            RETURNING id
        """, tender_id, cfg["formula"], json.dumps(cfg["params"], default=_jsonable),
             json.dumps(report, default=_jsonable), report_hash, actor_id)
        await append_audit(tx, tender_id, None, actor_id, "award_compute",
                           "award.runs", run_id, None,
                           {"report_hash": report_hash,
                            "winner": report["winners"][0] if len(winners) == 1 else None,
                            "tie": report["tie"]})

    return {"run_id": str(run_id), "report_hash": report_hash, "report": report}
