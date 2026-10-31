@dataclass
class BidIndex:
    sections: list[SectionChunk]      # heading-aware, like the tender side
    dense: VectorStore                # embeddings over sections
    bm25: BM25Okapi                   # lexical, over sections
    clause_echo: dict[str, list[str]] # tender clause_ref -> bid section ids
    toc: list[str]                    # section headings for navigation
