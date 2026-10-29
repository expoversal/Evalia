"""Industry-neutral computations for comparing submissions: price scores, totals, ranking,
sensitivity, outliers, identical values and the cheapest award across lots.

Everything here is deterministic. A model never performs any of these calculations.
"""
from __future__ import annotations

from itertools import product
from statistics import median
from typing import Literal

CorrectionRule = Literal["lower_of_stated_and_corrected", "corrected", "stated"]


def apply_correction_rule(stated: float, corrected: float, rule: CorrectionRule) -> float:
    """The figure a tender is evaluated at when its stated and corrected totals differ, under the tender's own rule."""
    if rule == "lower_of_stated_and_corrected":
        return min(stated, corrected)
    return corrected if rule == "corrected" else stated


def price_scores(prices: dict[str, float], max_points: float) -> dict[str, float]:
    """Lowest price scores the maximum; others score the maximum times lowest over their own price."""
    if not prices:
        return {}
    low = min(prices.values())
    return {k: round(max_points * low / v, 2) for k, v in prices.items()}


def ranking(totals: dict[str, float]) -> list[str]:
    return sorted(totals, key=lambda k: -totals[k])


def reweight(points: dict[str, dict[str, float]], maxima: dict[str, float], weights: dict[str, float]) -> dict[str, float]:
    """Total each subject under different stream weights: each stream's share of its maximum, times its weight."""
    return {s: round(sum(weights[g] * row.get(g, 0.0) / maxima[g] for g in weights if maxima.get(g)), 2)
            for s, row in points.items()}


def sensitivity(points: dict[str, dict[str, float]], maxima: dict[str, float],
                scenarios: dict[str, dict[str, float]]) -> dict[str, dict]:
    """Ranking under each weighting scenario, so the panel can see whether the first place depends on the weights."""
    out = {}
    for name, w in scenarios.items():
        totals = reweight(points, maxima, w)
        out[name] = {"weights": w, "totals": totals, "ranking": ranking(totals)}
    return out


def deviations_from_median(values: dict[str, float]) -> dict[str, float]:
    """Each value's fractional deviation from the median of all values (0.25 means 25 per cent above)."""
    if len(values) < 2:
        return {k: 0.0 for k in values}
    m = median(values.values())
    return {k: (v - m) / m if m else 0.0 for k, v in values.items()}


def identical_values(table: dict[str, dict[str, float]], min_matches: int) -> list[tuple[str, str, list[str]]]:
    """Pairs of subjects that share exactly the same value on at least `min_matches` keys."""
    subjects = sorted(table)
    hits = []
    for i, a in enumerate(subjects):
        for b in subjects[i + 1:]:
            same = [k for k in table[a] if k in table[b] and table[a][k] == table[b][k]]
            if len(same) >= min_matches:
                hits.append((a, b, same))
    return hits


def front_loading(series: list[float], share_of_duration: float) -> float:
    """Fraction of the total value forecast in the first `share_of_duration` of the periods."""
    total = sum(series)
    n = max(1, round(len(series) * share_of_duration))
    return sum(series[:n]) / total if total else 0.0


def cheapest_award(lot_prices: dict[str, dict[str, float]], combined: dict[str, float]) -> dict:
    """Compare the cheapest split award (any subject per lot) with the cheapest combined offer."""
    lots = sorted({lot for row in lot_prices.values() for lot in row})
    best_split, best_cost = None, float("inf")
    for choice in product(sorted(lot_prices), repeat=len(lots)):
        if all(lot in lot_prices[s] for s, lot in zip(choice, lots)):
            cost = sum(lot_prices[s][lot] for s, lot in zip(choice, lots))
            if cost < best_cost:
                best_split, best_cost = dict(zip(lots, choice)), cost
    best_combined = min(combined, key=combined.get) if combined else None
    return {"split": best_split, "split_cost": round(best_cost, 2) if best_split else None,
            "combined": best_combined, "combined_cost": combined.get(best_combined) if best_combined else None}
