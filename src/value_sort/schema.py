"""The Item contract. Downstream code may use these fields and nothing else."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Item(BaseModel):
    # strict: no type coercion ("5" is not 5); forbid: no fields beyond the contract.
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    parent_asin: str = Field(min_length=1)
    title: str
    price: float | None = Field(default=None, gt=0)
    average_rating: float | None = Field(default=None, ge=1, le=5)
    rating_number: int | None = Field(default=None, ge=0)
    details: dict[str, Any]
