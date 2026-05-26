"""Main application loop for the interactive cost splitter."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from . import ui
from .calculator import calculate_balances, calculate_settlement
from .models import Report, Spending
from .storage import ReportStorage
from .ui import Cancelled

_CENTS = Decimal("0.01")


def _collect_split(
    amount: Decimal, participants: list[str]
) -> dict[str, Decimal] | None:
    while True:
        split_type = ui.prompt_select(
            "Split type:", ["Equal", "Custom", "Percentage"]
        )

        if split_type == "Equal":
            return None

        if split_type == "Percentage":
            pcts: dict[str, Decimal] = {}
            for p in participants:
                pct_str = ui.prompt_text(f"Percentage for {p}:")
                pcts[p] = Decimal(pct_str)
            total_pct = sum(pcts.values())
            if total_pct != Decimal("100"):
                ui.print_error(
                    f"Percentages must sum to 100%, got {total_pct}%."
                )
                continue
            return {
                p: (amount * pct / Decimal("100")).quantize(
                    _CENTS, rounding=ROUND_HALF_UP
                )
                for p, pct in pcts.items()
            }

        # Custom amounts
        custom: dict[str, Decimal] = {}
        for p in participants:
            amt_str = ui.prompt_text(f"Amount for {p}:")
            custom[p] = Decimal(amt_str)
        total = sum(custom.values())
        if total != amount:
            ui.print_error(f"Amounts must sum to {amount}, got {total}.")
            continue
        return custom


class CostSplitterApp:
    def __init__(self, storage: ReportStorage | None = None) -> None:
        self.storage = storage or ReportStorage()

    def create_report(self) -> Report:
        name = ui.prompt_text("Report name:")
        raw = ui.prompt_text("Participants (comma-separated):")
        participants = [p.strip() for p in raw.split(",") if p.strip()]
        report = Report(name=name, participants=participants)
        self.storage.save(report)
        ui.print_success(
            f"Created report '{name}' with {len(participants)} participants."
        )
        return report

    def add_participant(self, report: Report) -> None:
        name = ui.prompt_text("New participant name:")
        name = name.strip()
        if name in report.participants:
            ui.print_error(f"'{name}' is already a participant.")
            return
        report.participants.append(name)
        self.storage.save(report)
        ui.print_success(f"Added participant '{name}'.")

    def add_spending(self, report: Report) -> None:
        description = ui.prompt_text("Description:")

        amount_str = ui.prompt_text("Amount:")
        try:
            amount = Decimal(amount_str)
        except InvalidOperation:
            ui.print_error(f"Invalid amount: {amount_str}")
            return

        paid_by = ui.prompt_select("Who paid?", report.participants)
        participants = ui.prompt_checkbox(
            "Who participates?", report.participants
        )

        if not participants:
            ui.print_error("At least one participant required.")
            return

        custom_amounts = _collect_split(amount, participants)

        spending = Spending(
            description=description,
            amount=amount,
            paid_by=paid_by,
            participants=participants,
            custom_amounts=custom_amounts,
        )
        report.spendings.append(spending)
        self.storage.save(report)
        ui.print_success(f"Added: {description} ({amount:.2f})")

    def edit_spending(self, report: Report) -> None:
        if not report.spendings:
            ui.print_info("No spendings to edit.")
            return

        choices = [
            {
                "name": f"{s.description} ({s.amount:.2f}, paid by {s.paid_by})",
                "value": i,
            }
            for i, s in enumerate(report.spendings)
        ]
        idx = ui.prompt_select("Edit which spending?", choices)
        old = report.spendings[idx]

        description = ui.prompt_text(f"Description [{old.description}]:")
        if not description.strip():
            description = old.description

        amount_str = ui.prompt_text(f"Amount [{old.amount}]:")
        try:
            amount = Decimal(amount_str) if amount_str.strip() else old.amount
        except InvalidOperation:
            ui.print_error(f"Invalid amount: {amount_str}")
            return

        paid_by = ui.prompt_select("Who paid?", report.participants)
        participants = ui.prompt_checkbox(
            "Who participates?", report.participants
        )

        if not participants:
            ui.print_error("At least one participant required.")
            return

        custom_amounts = _collect_split(amount, participants)

        report.spendings[idx] = Spending(
            description=description,
            amount=amount,
            paid_by=paid_by,
            participants=participants,
            custom_amounts=custom_amounts,
        )
        self.storage.save(report)
        ui.print_success(f"Updated: {description} ({amount:.2f})")

    def delete_spending(self, report: Report) -> None:
        if not report.spendings:
            ui.print_info("No spendings to delete.")
            return

        choices = [
            {
                "name": f"{s.description} ({s.amount:.2f}, paid by {s.paid_by})",
                "value": i,
            }
            for i, s in enumerate(report.spendings)
        ]
        idx = ui.prompt_select("Delete which spending?", choices)
        removed = report.spendings.pop(idx)
        self.storage.save(report)
        ui.print_success(f"Deleted: {removed.description}")

    def view_report(self, report: Report) -> None:
        ui.display_report(report)

    def settle(self, report: Report) -> None:
        balances = calculate_balances(report)
        transfers = calculate_settlement(report)
        ui.display_settlement(transfers, balances)

    def run(self) -> None:
        ui.print_info("Cost Splitter")

        slugs = self.storage.list_reports()
        action, slug = ui.prompt_report_selection(slugs)

        if action == "new":
            try:
                report = self.create_report()
            except Cancelled:
                ui.print_info("Cancelled.")
                return
        else:
            report = self.storage.load(slug)
            ui.print_success(
                f"Loaded '{report.name}' ({len(report.participants)} participants, "
                f"{len(report.spendings)} spendings)"
            )

        while True:
            choice = ui.prompt_action()
            if choice == "quit":
                ui.print_info("Goodbye!")
                break

            try:
                if choice == "add":
                    self.add_spending(report)
                elif choice == "report":
                    self.view_report(report)
                elif choice == "settle":
                    self.settle(report)
                elif choice == "delete":
                    self.delete_spending(report)
                elif choice == "edit":
                    self.edit_spending(report)
                elif choice == "participant":
                    self.add_participant(report)
            except Cancelled:
                ui.print_info("Cancelled.")
