# app/auth/deps.py
from fastapi import Depends, HTTPException, Header
from app.auth.jwt import Claims, verify
from app.auth.policy import READ_POLICY, WRITE_POLICY, Role
from app.db import db

async def current_user(authorization: str = Header(...)) -> Claims:
    token = authorization.removeprefix("Bearer ").strip()
    return verify(token, settings.JWT_SECRET)

async def _envelope_sealed(tender_id: str, envelope: str) -> bool:
    schema = "technical" if envelope == "technical" else "commercial"
    row = await db.fetchval(f"""
        SELECT 1 FROM {schema}.seals
        WHERE tender_id = $1 AND revoked_at IS NULL
        LIMIT 1
    """, tender_id)
    return row is not None

def require_read(envelope: str):
    async def _dep(user: Claims = Depends(current_user),
                   tender_id: str = None) -> Claims:   # tender_id from path
        role = Role(user.role)
        if envelope not in READ_POLICY[role]:
            raise HTTPException(403, f"role {role.value} cannot read {envelope}")
        # lead is locked to one envelope per session
        if role == Role.EVALUATION_LEAD:
            if user.envelope_scope != envelope:
                raise HTTPException(423,
                    f"lead session is locked to {user.envelope_scope or 'none'}; "
                    f"re-auth with envelope_scope={envelope} to switch")
        # commercial read requires technical seal — the hard lock
        if envelope == "commercial":
            if not await _envelope_sealed(tender_id, "technical"):
                raise HTTPException(423,
                    "technical envelope not sealed; commercial is locked")
        return user
    return _dep

def require_write(envelope: str):
    async def _dep(user: Claims = Depends(current_user),
                   tender_id: str = None) -> Claims:
        role = Role(user.role)
        if envelope not in WRITE_POLICY[role]:
            raise HTTPException(403, f"role {role.value} cannot write {envelope}")
        # sealed envelopes reject writes at the API layer, DB layer enforces too (§3.3)
        if await _envelope_sealed(tender_id, envelope):
            raise HTTPException(423, f"{envelope} envelope is sealed")
        return user
    return _dep
