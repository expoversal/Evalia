import re
from docling.document_converter import DocumentConverter

CLAUSE_PATTERNS = [
    r"^(?:Clause|Cl\.?)\s*(\d+(?:\.\d+)*)",           # PSSCOC
    r"^(\d+(?:\.\d+){1,4})\s+\S",                      # spec numbering 03 30 00 / 2.3.1
    r"^Section\s+(\d+[A-Z]?)",
    r"^(\d+\.\d+)\s+[A-Z]",                            # form/schedule items
]

def chunk_by_clause(doc) -> list[ClauseChunk]:
    chunks, current = [], None
    for block in doc.iterate_blocks():                 # Docling gives typed blocks
        heading = _match_clause_heading(block.text)
        if heading:
            if current: chunks.append(current)
            current = ClauseChunk(
                doc_id=doc.id,
                path=doc.path_to(block),
                clause_ref=heading,
                text=block.text,
                page=block.page,
                section_type=_classify_section(doc.path_to(block)),
                is_table=False,
                parent_ref=doc.parent_clause_of(heading),
            )
        elif current:
            current.text += "\n" + block.text
            current.is_table |= block.type == "table"
    if current: chunks.append(current)

    # attach parent text for cross-reference resolution
    return _attach_parent_context(chunks)
