class BQRow(BaseModel):
    item: str
    description: str
    unit: str
    qty: float
    rate: float
    amount: float

def check_bq(rows: list[BQRow], tolerance=0.01) -> dict:
    issues = []
    for r in rows:
        expected = round(r.qty * r.rate, 2)
        if abs(expected - r.amount) > tolerance:
            issues.append({"item": r.item, "type": "extension_error",
                           "expected": expected, "stated": r.amount})
    stated_total = sum(r.amount for r in rows)
    return {"total": stated_total, "issues": issues,
            "issue_count": len(issues), "rows": len(rows)}
