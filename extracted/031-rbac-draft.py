from fastapi import Depends, HTTPException, Request
from enum import Enum

class Role(str, Enum):
    TECHNICAL_EVALUATOR = "technical_evaluator"
    COMMERCIAL_EVALUATOR = "commercial_evaluator"
    EVALUATION_LEAD = "evaluation_lead"
    PROCUREMENT_OFFICER = "procurement_officer"
    AUDITOR = "auditor"
    ADMIN = "admin"

ENVELOPE_ACCESS = {
    Role.TECHNICAL_EVALUATOR: {"technical"},
    Role.COMMERCIAL_EVALUATOR: {"commercial"},
    Role.EVALUATION_LEAD: {"technical", "commercial"},  # but not simultaneously
    Role.PROCUREMENT_OFFICER: set(),  # no direct read; receives results
    Role.AUDITOR: {"technical", "commercial"},  # read-only
    Role.ADMIN: set(),  # no envelope access at all
}

def require_envelope(envelope: str):
    def _check(user: User = Depends(current_user)):
        allowed = ENVELOPE_ACCESS.get(Role(user.role), set())
        if envelope not in allowed:
            raise HTTPException(403, f"role {user.role} cannot access {envelope} envelope")
        return user
    return _check
