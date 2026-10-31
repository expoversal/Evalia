import numpy as np

def flag_abnormal_rates(rate_matrix: dict[str, dict[str, float]],
                        floor_pct=0.70, iqr_k=1.5) -> list[dict]:
    """
    rate_matrix: {bidder_id: {item_code: rate}}
    Flags a bidder/item when the rate is far below the peer distribution.
    """
    items = {i for b in rate_matrix.values() for i in b}
    flags = []
    for item in items:
        rates = {b: m[item] for b, m in rate_matrix.items() if item in m}
        if len(rates) < 4:                       # too few bidders to judge
            continue
        vals = np.array(list(rates.values()))
        median = float(np.median(vals))
        q1, q3 = np.percentile(vals, [25, 75])
        iqr = q3 - q1
        for bidder, r in rates.items():
            if r < median * floor_pct or (iqr > 0 and r < q1 - iqr_k * iqr):
                flags.append({"bidder": bidder, "item": item, "rate": r,
                              "median": median,
                              "pct_of_median": round(r / median, 3)})
    return flags
