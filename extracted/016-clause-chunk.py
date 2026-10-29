from dataclasses import dataclass, field

@dataclass
class ClauseChunk:
    doc_id: str
    path: list[str]          # ["PSSCOC", "Cl. 4", "4.2", "4.2.3"]
    clause_ref: str          # canonical: "PSSCOC 4.2.3"
    text: str
    page: int
    section_type: str        # conditions | spec | instruction | schedule | form | appendix
    is_table: bool
    parent_ref: str | None   # "PSSCOC 4.2" — for inherited context
