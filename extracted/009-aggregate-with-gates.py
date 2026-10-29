def aggregate(scores: dict[str, CriterionScore], rubric) -> dict:
    # 1. gates first — a failed gate is disqualifying, not a deduction
    gate_results = evaluate_gates(rubric.gates, scores)
    if not all(gate_results.values()):
        return {"status": "non_compliant", "gates": gate_results}

    # 2. weighted score over scored criteria only
    scored = [c for c in rubric.criteria if c.type == "scored"]
    total_w = sum(c.weight for c in scored)
    raw = sum(scores[c.id].score * c.weight for c in scored) / total_w
    return {
        "status": "evaluated",
        "weighted_score": round(raw, 2),
        "gates": gate_results,
        "low_confidence": [c.id for c in scored
                           if scores[c.id].confidence == "low"],
    }
