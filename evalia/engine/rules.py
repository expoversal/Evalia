"""Deterministic scoring rules, configured by the client and signed off before any submission is read.

The rules are industry-neutral: they count records that meet filters, or map a
value to points through bands. A pack supplies the field names and defaults.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class RecordRule(BaseModel):
    """Award points for each record that passes every filter, up to a maximum number of records."""

    id: str
    title: str
    keyword_field: str
    keywords: list[str]
    year_field: str
    year_min: int
    year_max: int
    value_field: str
    value_min: float
    rating_field: str
    rating_scale: list[str] = Field(description="Ordered from worst to best")
    rating_min: str
    role_field: str
    role_required: str | None = None
    points_per_record: float
    max_records: int
    min_records: int = 0

    @property
    def max_points(self) -> float:
        return self.points_per_record * self.max_records

    def check(self, record: dict) -> list[str]:
        """Return the reasons a record fails. An empty list means it qualifies."""
        reasons: list[str] = []
        label = lambda f: f.replace("_", " ")  # noqa: E731
        kw = str(record.get(self.keyword_field, "")).lower()
        if not any(k.lower() in kw for k in self.keywords):
            reasons.append(f"{label(self.keyword_field)} '{record.get(self.keyword_field)}' matches none of: {', '.join(self.keywords)}")
        year = record.get(self.year_field)
        if not isinstance(year, int) or not (self.year_min <= year <= self.year_max):
            reasons.append(f"{label(self.year_field)} {year} is outside {self.year_min} to {self.year_max}")
        value = record.get(self.value_field)
        if not isinstance(value, (int, float)) or value < self.value_min:
            reasons.append(f"{label(self.value_field)} {value:,.0f} is below the minimum of {self.value_min:,.0f}" if isinstance(value, (int, float))
                           else f"{label(self.value_field)} not stated")
        rating = record.get(self.rating_field)
        if rating not in self.rating_scale:
            reasons.append(f"{label(self.rating_field)} not evidenced")
        elif self.rating_scale.index(rating) < self.rating_scale.index(self.rating_min):
            reasons.append(f"{label(self.rating_field)} '{rating}' is below the minimum of '{self.rating_min}'")
        if self.role_required:
            role = str(record.get(self.role_field, ""))
            if self.role_required.lower() not in role.lower():
                reasons.append(f"{label(self.role_field)} '{role}' is not '{self.role_required}'")
        return reasons


class Band(BaseModel):
    up_to: float | None = Field(description="Inclusive upper bound; None means no upper bound")
    points: float


class BandRule(BaseModel):
    """Map a single numeric value to points. Bands are checked in order."""

    id: str
    title: str
    field: str
    bands: list[Band]

    @property
    def max_points(self) -> float:
        return max(b.points for b in self.bands)

    def points_for(self, value: float) -> float:
        for b in self.bands:
            if b.up_to is None or value <= b.up_to:
                return b.points
        return 0.0


def capped_total(points: list[float], cap: float) -> float:
    return min(sum(points), cap)
