# app/auth/policy.py
from enum import Enum

class Role(str, Enum):
    TECHNICAL_EVALUATOR  = "technical_evaluator"
    COMMERCIAL_EVALUATOR = "commercial_evaluator"
    EVALUATION_LEAD      = "evaluation_lead"
    PROCUREMENT_OFFICER  = "procurement_officer"
    AUDITOR              = "auditor"
    ADMIN                = "admin"

# What envelope each role may READ
READ_POLICY: dict[Role, set[str]] = {
    Role.TECHNICAL_EVALUATOR:  {"technical"},
    Role.COMMERCIAL_EVALUATOR: {"commercial"},
    Role.EVALUATION_LEAD:      {"technical", "commercial"},   # gated — see §2.4
    Role.PROCUREMENT_OFFICER:  set(),                         # sees results only
    Role.AUDITOR:              {"technical", "commercial"},   # read-only
    Role.ADMIN:                set(),                         # never sees envelope content
}

# What envelope each role may WRITE (i.e. propose/override)
WRITE_POLICY: dict[Role, set[str]] = {
    Role.TECHNICAL_EVALUATOR:  {"technical"},
    Role.COMMERCIAL_EVALUATOR: {"commercial"},
    Role.EVALUATION_LEAD:      set(),   # lead seals, does not score — separation of duty
    Role.PROCUREMENT_OFFICER:  set(),
    Role.AUDITOR:              set(),
    Role.ADMIN:                set(),
}

# Who may SEAL / UNSEAL
SEAL_ROLES = {Role.EVALUATION_LEAD}
UNSEAL_ROLES = {Role.EVALUATION_LEAD}   # requires co-sign from PROCUREMENT_OFFICER — §9
