"""Amounts written in words, for the words-against-figures check. Industry-neutral; English number words only."""
from __future__ import annotations

import re

_UNITS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
    "seventeen eighteen nineteen".split())}
_TENS = {w: 10 * i for i, w in enumerate("_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()) if w != "_"}
_SCALES = {"thousand": 1_000, "million": 1_000_000, "billion": 1_000_000_000}


def words_to_number(text: str) -> float | None:
    """Parse an amount such as "Nineteen million five hundred fifty-six thousand dollars". None if it cannot be read."""
    total = current = 0
    seen = False
    for w in re.findall(r"[a-z]+", text.lower().replace("-", " ")):
        if w in _UNITS:
            current += _UNITS[w]
        elif w in _TENS:
            current += _TENS[w]
        elif w == "hundred":
            current = (current or 1) * 100
        elif w in _SCALES:
            total += (current or 1) * _SCALES[w]
            current = 0
        elif w in ("and", "dollars", "dollar", "only", "us"):
            continue
        else:
            return None
        seen = True
    return float(total + current) if seen else None
