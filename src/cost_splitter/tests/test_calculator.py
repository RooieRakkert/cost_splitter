"""Tests for cost_splitter settlement calculator."""

from __future__ import annotations

from decimal import Decimal

from ..calculator import (
    calculate_balances,
    calculate_settlement,
)
from ..models import Report, Spending, Transfer


def _report(*spendings: Spending, participants: list[str] | None = None) -> Report:
    if participants is None:
        participants = sorted(
            {s.paid_by for s in spendings}
            | {p for s in spendings for p in s.participants}
        )
    r = Report(name="Test", participants=participants)
    r.spendings.extend(spendings)
    return r


class TestCalculateBalances:
    def test_simple_two_person_equal_split(self) -> None:
        report = _report(
            Spending(
                description="Dinner",
                amount=Decimal("20.00"),
                paid_by="Bouke",
                participants=["Bouke", "Jan"],
            )
        )
        balances = calculate_balances(report)
        assert balances["Bouke"] == Decimal("10.00")
        assert balances["Jan"] == Decimal("-10.00")

    def test_three_person_equal_split(self) -> None:
        report = _report(
            Spending(
                description="Dinner",
                amount=Decimal("60.00"),
                paid_by="Bouke",
                participants=["Bouke", "Jan", "Karel"],
            )
        )
        balances = calculate_balances(report)
        assert balances["Bouke"] == Decimal("40.00")
        assert balances["Jan"] == Decimal("-20.00")
        assert balances["Karel"] == Decimal("-20.00")

    def test_custom_amounts(self) -> None:
        report = _report(
            Spending(
                description="Hotel",
                amount=Decimal("100.00"),
                paid_by="Jan",
                participants=["Jan", "Karel"],
                custom_amounts={"Jan": Decimal("60.00"), "Karel": Decimal("40.00")},
            )
        )
        balances = calculate_balances(report)
        assert balances["Jan"] == Decimal("40.00")
        assert balances["Karel"] == Decimal("-40.00")

    def test_multiple_spendings(self) -> None:
        report = _report(
            Spending(
                description="Dinner",
                amount=Decimal("30.00"),
                paid_by="Bouke",
                participants=["Bouke", "Jan"],
            ),
            Spending(
                description="Taxi",
                amount=Decimal("20.00"),
                paid_by="Jan",
                participants=["Bouke", "Jan"],
            ),
        )
        balances = calculate_balances(report)
        # Bouke: paid 30, owes 15+10=25 -> net +5
        # Jan: paid 20, owes 15+10=25 -> net -5
        assert balances["Bouke"] == Decimal("5.00")
        assert balances["Jan"] == Decimal("-5.00")

    def test_all_balanced(self) -> None:
        report = _report(
            Spending(
                description="A pays",
                amount=Decimal("10.00"),
                paid_by="A",
                participants=["A", "B"],
            ),
            Spending(
                description="B pays",
                amount=Decimal("10.00"),
                paid_by="B",
                participants=["A", "B"],
            ),
        )
        balances = calculate_balances(report)
        assert balances["A"] == Decimal("0.00")
        assert balances["B"] == Decimal("0.00")

    def test_single_person(self) -> None:
        report = _report(
            Spending(
                description="Solo",
                amount=Decimal("50.00"),
                paid_by="A",
                participants=["A"],
            )
        )
        balances = calculate_balances(report)
        assert balances["A"] == Decimal("0.00")

    def test_no_spendings(self) -> None:
        report = Report(name="Empty", participants=["A", "B"])
        balances = calculate_balances(report)
        assert balances["A"] == Decimal("0.00")
        assert balances["B"] == Decimal("0.00")

    def test_payer_not_participant(self) -> None:
        report = _report(
            Spending(
                description="Gift",
                amount=Decimal("30.00"),
                paid_by="Bouke",
                participants=["Jan", "Karel"],
            ),
            participants=["Bouke", "Jan", "Karel"],
        )
        balances = calculate_balances(report)
        assert balances["Bouke"] == Decimal("30.00")
        assert balances["Jan"] == Decimal("-15.00")
        assert balances["Karel"] == Decimal("-15.00")


class TestCalculateSettlement:
    def test_simple_settlement(self) -> None:
        report = _report(
            Spending(
                description="Dinner",
                amount=Decimal("20.00"),
                paid_by="Bouke",
                participants=["Bouke", "Jan"],
            )
        )
        transfers = calculate_settlement(report)
        assert len(transfers) == 1
        assert transfers[0] == Transfer(
            from_person="Jan", to_person="Bouke", amount=Decimal("10.00")
        )

    def test_no_transfers_when_balanced(self) -> None:
        report = _report(
            Spending(
                description="A pays",
                amount=Decimal("10.00"),
                paid_by="A",
                participants=["A", "B"],
            ),
            Spending(
                description="B pays",
                amount=Decimal("10.00"),
                paid_by="B",
                participants=["A", "B"],
            ),
        )
        transfers = calculate_settlement(report)
        assert transfers == []

    def test_debt_simplification(self) -> None:
        # A owes B 10, B owes C 10 → should simplify to A owes C 10
        report = _report(
            Spending(
                description="B pays for A+B",
                amount=Decimal("20.00"),
                paid_by="B",
                participants=["A", "B"],
            ),
            Spending(
                description="C pays for B+C",
                amount=Decimal("20.00"),
                paid_by="C",
                participants=["B", "C"],
            ),
        )
        transfers = calculate_settlement(report)
        assert len(transfers) == 1
        assert transfers[0] == Transfer(
            from_person="A", to_person="C", amount=Decimal("10.00")
        )

    def test_three_person_settlement(self) -> None:
        report = _report(
            Spending(
                description="Big dinner",
                amount=Decimal("90.00"),
                paid_by="Bouke",
                participants=["Bouke", "Jan", "Karel"],
            )
        )
        transfers = calculate_settlement(report)
        assert len(transfers) == 2
        total_paid_to_bouke = sum(t.amount for t in transfers if t.to_person == "Bouke")
        assert total_paid_to_bouke == Decimal("60.00")

    def test_empty_report(self) -> None:
        report = Report(name="Empty", participants=["A", "B"])
        transfers = calculate_settlement(report)
        assert transfers == []

    def test_single_payer_for_everything(self) -> None:
        report = _report(
            Spending(
                description="Everything",
                amount=Decimal("100.00"),
                paid_by="Bouke",
                participants=["Bouke", "Jan", "Karel"],
            ),
            Spending(
                description="More stuff",
                amount=Decimal("50.00"),
                paid_by="Bouke",
                participants=["Bouke", "Jan", "Karel"],
            ),
        )
        transfers = calculate_settlement(report)
        total = sum(t.amount for t in transfers)
        assert total == Decimal("100.00")
        assert all(t.to_person == "Bouke" for t in transfers)

    def test_transfer_amounts_are_rounded_to_cents(self) -> None:
        report = _report(
            Spending(
                description="Odd split",
                amount=Decimal("10.00"),
                paid_by="A",
                participants=["A", "B", "C"],
            )
        )
        transfers = calculate_settlement(report)
        for t in transfers:
            assert t.amount == t.amount.quantize(Decimal("0.01"))
