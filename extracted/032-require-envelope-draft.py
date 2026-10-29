async def require_envelope(envelope: str, tender_id: str, user: User):
    allowed = ENVELOPE_ACCESS[Role(user.role)]
    if envelope not in allowed:
        raise HTTPException(403)
    if envelope == "commercial":
        tech_seal = await get_seal(tender_id, "technical")
        if not tech_seal:
            raise HTTPException(423, "technical envelope not sealed; commercial locked")
    return user
