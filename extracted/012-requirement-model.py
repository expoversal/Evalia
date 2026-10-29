class Requirement(BaseModel):
    req_id: str
    clause_ref: str            # "PSSCOC cl. 4.2" / "Spec 03300 §2.3"
    text: str                  # normalised requirement statement
    mandatory: bool
    category: Literal["document","technical","personnel","programme","commercial"]

async def extract_requirements(tender_doc_chunks, llm) -> list[Requirement]:
    # per-section extraction, then dedupe by clause_ref + text hash
    ...
