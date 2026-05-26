"""Pydantic data models for cost splitting."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal  # noqa: TC003

from pydantic import BaseModel, Field, field_validator, model_validator


class Spending(BaseModel):
    description: str
    amount: Decimal = Field(gt=0)
    paid_by: str
    participants: list[str] = Field(min_length=1)
    custom_amounts: dict[str, Decimal] | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @model_validator(mode="after")
    def validate_custom_amounts(self) -> Spending:
        if self.custom_amounts is None:
            return self
        if set(self.custom_amounts.keys()) != set(self.participants):
            raise ValueError("custom_amounts keys must match participants exactly")
        if sum(self.custom_amounts.values()) != self.amount:
            raise ValueError(
                f"custom_amounts must sum to {self.amount}, got {sum(self.custom_amounts.values())}"
            )
        return self


class Report(BaseModel):
    name: str
    participants: list[str] = Field(min_length=1)
    spendings: list[Spending] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @field_validator("participants")
    @classmethod
    def participants_must_be_unique(cls, v: list[str]) -> list[str]:
        if len(v) != len(set(v)):
            raise ValueError("participants must be unique")
        return v

    @property
    def slug(self) -> str:
        return re.sub(r"[^a-z0-9]+", "-", self.name.lower()).strip("-")


class Transfer(BaseModel):
    from_person: str
    to_person: str
    amount: Decimal = Field(gt=0)
