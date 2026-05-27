"""Balance calculation and debt simplification for cost splitting."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from .models import CENTS, Report, Transfer


def calculate_balances(report: Report) -> dict[str, Decimal]:
    balances: dict[str, Decimal] = {p: Decimal("0.00") for p in report.participants}

    for spending in report.spendings:
        balances[spending.paid_by] += spending.amount

        if spending.custom_amounts:
            for person, amount in spending.custom_amounts.items():
                balances[person] -= amount
        else:
            share = (spending.amount / len(spending.participants)).quantize(
                CENTS, rounding=ROUND_HALF_UP
            )
            for i, person in enumerate(spending.participants):
                if i == len(spending.participants) - 1:
                    remainder = spending.amount - share * (
                        len(spending.participants) - 1
                    )
                    balances[person] -= remainder
                else:
                    balances[person] -= share

    return balances


def calculate_settlement(report: Report) -> list[Transfer]:
    balances = calculate_balances(report)

    debtors: list[tuple[str, Decimal]] = []
    creditors: list[tuple[str, Decimal]] = []

    for person, balance in balances.items():
        if balance < 0:
            debtors.append((person, -balance))
        elif balance > 0:
            creditors.append((person, balance))

    debtors.sort(key=lambda x: x[1], reverse=True)
    creditors.sort(key=lambda x: x[1], reverse=True)

    transfers: list[Transfer] = []
    di, ci = 0, 0

    while di < len(debtors) and ci < len(creditors):
        debtor, debt = debtors[di]
        creditor, credit = creditors[ci]
        amount = min(debt, credit).quantize(CENTS, rounding=ROUND_HALF_UP)

        if amount > 0:
            transfers.append(
                Transfer(from_person=debtor, to_person=creditor, amount=amount)
            )

        debt -= amount
        credit -= amount
        debtors[di] = (debtor, debt)
        creditors[ci] = (creditor, credit)

        if debt == 0:
            di += 1
        if credit == 0:
            ci += 1

    return transfers
