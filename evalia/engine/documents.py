"""Document ingestion with page-level provenance."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber


@dataclass(frozen=True)
class Page:
    number: int  # 1-based, as a reader would cite it
    text: str
    tables: tuple[tuple[tuple[str, ...], ...], ...] = ()


@dataclass
class Document:
    doc_id: str
    path: Path
    sha256: str
    pages: list[Page] = field(default_factory=list)

    def page(self, number: int) -> Page | None:
        if 1 <= number <= len(self.pages):
            return self.pages[number - 1]
        return None

    @property
    def pages_without_text(self) -> list[int]:
        return [p.number for p in self.pages if not p.text.strip()]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_pdf(path: str | Path, doc_id: str | None = None) -> Document:
    """Read a PDF's text layer page by page. Pages without text are kept and reported, not dropped."""
    path = Path(path)
    doc = Document(doc_id=doc_id or path.stem, path=path, sha256=sha256_file(path))
    with pdfplumber.open(path) as pdf:
        for i, pg in enumerate(pdf.pages, 1):
            text = pg.extract_text() or ""
            tables = tuple(
                tuple(tuple((cell or "").strip() for cell in row) for row in table)
                for table in (pg.extract_tables() or [])
            )
            doc.pages.append(Page(number=i, text=text, tables=tables))
    return doc
