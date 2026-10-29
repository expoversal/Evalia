# award/formulas.py
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

@dataclass
class BidderResult:
    bidder_id: str
    bidder_name: str
    passed_gates: bool
    compliance_summary: dict        # {'non_compliant': n, 'not_addressed': n, ...}
    technical_score: Decimal        # weighted 0..scale_max
    evaluated_price: Decimal | None
    fee_score: Decimal | None       # 0..100
    final_score: Decimal | None
    rank: int | None
    ineligible_reason: str | None

def _d(x) -> Decimal:
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

# ── Lowest Compliant Price ──────────────────────────────────────────
# Eligible = passed gates AND no disqualifying non-compliance on mandatory reqs
# Winner = lowest evaluated_price among eligible
def lcp(packages: list[dict], config: dict) -> list[BidderResult]:
    results = [_base_result(p) for p in packages]
    eligible = [r for r in results if r.passed_gates and r.ineligible_reason is None
                and r.evaluated_price is not None]
    if not eligible:
        return results
    winner = min(eligible, key=lambda r: r.evaluated_price)
    for i, r in enumerate(sorted(eligible, key=lambda r: r.evaluated_price), 1):
        r.rank = i
        r.final_score = r.evaluated_price
    winner.rank = 1
    return results

# ── Quality-Fee Method (Singapore MOF style) ────────────────────────
# Q = technical score normalised to 0..100
# F = 100 * (lowest_fee / bidder_fee)    [inverse linear, floor 0]
# Final = w_q * Q + w_f * F              [weights sum to 1, e.g. 0.7 / 0.3]
# Winner = highest Final
def qfm(packages: list[dict], config: dict) -> list[BidderResult]:
    w_q = Decimal(str(config.get("quality_weight", "0.7")))
    w_f = Decimal("1") - w_q
    scale_max = Decimal(str(config.get("scale_max", "100")))

    results = [_base_result(p) for p in packages]
    eligible = [r for r in results if r.passed_gates and r.ineligible_reason is None
                and r.evaluated_price and r.evaluated_price > 0]
    if not eligible:
        return results

    lowest_fee = min(r.evaluated_price for r in eligible)
    for r in eligible:
        r.fee_score = _d(Decimal("100") * lowest_fee / r.evaluated_price)
        q_norm = _d(r.technical_score * Decimal("100") / scale_max)
        r.final_score = _d(w_q * q_norm + w_f * r.fee_score)

    for i, r in enumerate(sorted(eligible, key=lambda r: r.final_score, reverse=True), 1):
        r.rank = i
    return results

# ── Price-Quality Method (weighted normalised) ──────────────────────
# score = w_q * (Q / Q_ref) + w_p * (P_min / P)
# Q_ref = configurable (either "observed_max" or an absolute reference)
# Winner = highest score
def pqm(packages: list[dict], config: dict) -> list[BidderResult]:
    w_q = Decimal(str(config.get("quality_weight", "0.6")))
    w_p = Decimal("1") - w_q
    q_ref_mode = config.get("quality_reference", "observed_max")

    results = [_base_result(p) for p in packages]
    eligible = [r for r in results if r.passed_gates and r.ineligible_reason is None
                and r.evaluated_price and r.evaluated_price > 0]
    if not eligible:
        return results

    if q_ref_mode == "observed_max":
        q_ref = max(r.technical_score for r in eligible) or Decimal("1")
    else:
        q_ref = Decimal(str(config.get("quality_reference_value", "100")))

    p_min = min(r.evaluated_price for r in eligible)
    for r in eligible:
        q_norm = r.technical_score / q_ref if q_ref > 0 else Decimal("0")
        p_norm = p_min / r.evaluated_price
        r.final_score = _d(w_q * q_norm + w_p * p_norm)
        r.fee_score = None

    for i, r in enumerate(sorted(eligible, key=lambda r: r.final_score, reverse=True), 1):
        r.rank = i
    return results

# ── shared helpers ──────────────────────────────────────────────────
def _base_result(package: dict) -> BidderResult:
    comp = package["compliance"] or []
    summary = {"compliant": 0, "partial": 0, "non_compliant": 0,
               "not_addressed": 0, "not_applicable": 0}
    for row in comp:
        summary[row["status"]] = summary.get(row["status"], 0) + 1

    # disqualifying = any mandatory non_compliant (not partial, not not_addressed)
    # partial/not_addressed on mandatory → "query to bidder", not automatic DQ
    # (adjust to your procurement rules; some codes auto-DQ on not_addressed)
    dq = any(
        row["mandatory"] and row["status"] == "non_compliant"
        for row in comp
    )
    tech = Decimal("0")
    scores = package["criterion_scores"] or []
    total_w = sum((Decimal(str(c["weight"])) for c in scores), Decimal("0"))
    if total_w > 0:
        tech = sum(
            (Decimal(str(c["human_score"] or 0)) * Decimal(str(c["weight"]))
             for c in scores), Decimal("0")
        ) / total_w

    return BidderResult(
        bidder_id=package["bidder_id"],
        bidder_name=package["bidder_name"],
        passed_gates=package["gates_passed"],
        compliance_summary=summary,
        technical_score=_d(tech),
        evaluated_price=(_d(package["evaluated_price"])
                         if package["evaluated_price"] is not None else None),
        fee_score=None,
        final_score=None,
        rank=None,
        ineligible_reason=("failed_gates" if not package["gates_passed"]
                          else "disqualifying_non_compliance" if dq
                          else None),
    )

FORMULAS = {"lcp": lcp, "qfm": qfm, "pqm": pqm}
