@dataclass
class MatrixMetrics:
    fn_rate_mandatory: float     # missed non-compliance — THE metric
    fp_rate: float               # false non-compliance — erodes trust
    status_agreement: float      # vs human panel, weighted kappa
    evidence_verified_pct: float
    needs_clarification_rate: float   # high = context problem, not model problem
