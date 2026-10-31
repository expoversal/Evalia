"""Quote verification: a quote counts as evidence only if it appears on the page it cites."""
from __future__ import annotations

import re

from .documents import Document

_SPACE = re.compile(r"\s+")
_FOLD = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", " ": " "})


def normalise(text: str) -> str:
    """Collapse whitespace and fold typographic quotes and dashes. Case and wording are preserved."""
    return _SPACE.sub(" ", text.translate(_FOLD)).strip()


def quote_on_page(doc: Document, page: int, quote: str) -> bool:
    """True only if the quote occurs verbatim, after normalisation, on the cited page."""
    q = normalise(quote)
    pg = doc.page(page)
    if not q or pg is None:
        return False
    return q in normalise(pg.text)


def find_quote(doc: Document, quote: str) -> int | None:
    """Return the first page on which the quote occurs, or None."""
    q = normalise(quote)
    for pg in doc.pages:
        if q and q in normalise(pg.text):
            return pg.number
    return None
