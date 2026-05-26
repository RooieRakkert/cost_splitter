"""Tests for cost_splitter data models."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from ..models import Report, Spending, Transfer


class TestSpending:
    def test_create_equal_split(self) -> None:
        s = Spending(
            description="Dinner",
            amount=Decimal("60.00"),
            paid_by="Bouke",
            participants=["Bouke", "Jan", "Karel"],
        )
        assert s.description == "Dinner"
        assert s.amount == Decimal("60.00")
        assert s.paid_by == "Bouke"
        assert s.participants == ["Bouke", "Jan", "Karel"]
        assert s.custom_amounts is None
        assert s.created_at is not None

    def test_create_custom_split(self) -> None:
        s = Spending(
            description="Hotel",
            amount=Decimal("100.00"),
            paid_by="Jan",
            participants=["Jan", "Karel"],
            custom_amounts={"Jan": Decimal("60.00"), "Karel": Decimal("40.00")},
        )
        assert s.custom_amounts == {"Jan": Decimal("60.00"), "Karel": Decimal("40.00")}

    def test_custom_amounts_must_sum_to_total(self) -> None:
        with pytest.raises(ValidationError, match="custom_amounts"):
            Spending(
                description="Drinks",
                amount=Decimal("50.00"),
                paid_by="Bouke",
                participants=["Bouke", "Jan"],
                custom_amounts={"Bouke": Decimal("20.00"), "Jan": Decimal("20.00")},
            )

    def test_custom_amounts_keys_must_match_participants(self) -> None:
        with pytest.raises(ValidationError, match="custom_amounts"):
            Spending(
                description="Drinks",
                amount=Decimal("50.00"),
                paid_by="Bouke",
                participants=["Bouke", "Jan"],
                custom_amounts={"Bouke": Decimal("25.00"), "Karel": Decimal("25.00")},
            )

    def test_amount_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            Spending(
                description="Refund",
                amount=Decimal("-10.00"),
                paid_by="Bouke",
                participants=["Bouke"],
            )

    def test_participants_not_empty(self) -> None:
        with pytest.raises(ValidationError):
            Spending(
                description="Solo",
                amount=Decimal("10.00"),
                paid_by="Bouke",
                participants=[],
            )

    def test_default_created_at(self) -> None:
        before = datetime.now(tz=timezone.utc)
        s = Spending(
            description="Test",
            amount=Decimal("10.00"),
            paid_by="A",
            participants=["A"],
        )
        after = datetime.now(tz=timezone.utc)
        assert before <= s.created_at <= after


class TestReport:
    def test_create_report(self) -> None:
        r = Report(name="Holiday Trip", participants=["Bouke", "Jan", "Karel"])
        assert r.name == "Holiday Trip"
        assert r.participants == ["Bouke", "Jan", "Karel"]
        assert r.spendings == []
        assert r.created_at is not None

    def test_participants_must_be_unique(self) -> None:
        with pytest.raises(ValidationError, match="unique"):
            Report(name="Test", participants=["Bouke", "Bouke", "Jan"])

    def test_participants_not_empty(self) -> None:
        with pytest.raises(ValidationError):
            Report(name="Empty", participants=[])

    def test_add_spending(self) -> None:
        r = Report(name="Trip", participants=["Bouke", "Jan"])
        s = Spending(
            description="Lunch",
            amount=Decimal("20.00"),
            paid_by="Bouke",
            participants=["Bouke", "Jan"],
        )
        r.spendings.append(s)
        assert len(r.spendings) == 1

    def test_slug(self) -> None:
        r = Report(name="Holiday Trip 2026!", participants=["A", "B"])
        assert r.slug == "holiday-trip-2026"

    def test_json_round_trip(self) -> None:
        r = Report(name="Test", participants=["A", "B"])
        r.spendings.append(
            Spending(
                description="Item",
                amount=Decimal("30.00"),
                paid_by="A",
                participants=["A", "B"],
            )
        )
        json_str = r.model_dump_json()
        r2 = Report.model_validate_json(json_str)
        assert r2.name == r.name
        assert r2.participants == r.participants
        assert len(r2.spendings) == 1
        assert r2.spendings[0].amount == Decimal("30.00")


class TestTransfer:
    def test_create_transfer(self) -> None:
        t = Transfer(from_person="Jan", to_person="Bouke", amount=Decimal("10.00"))
        assert t.from_person == "Jan"
        assert t.to_person == "Bouke"
        assert t.amount == Decimal("10.00")

    def test_amount_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            Transfer(from_person="Jan", to_person="Bouke", amount=Decimal("-5.00"))
