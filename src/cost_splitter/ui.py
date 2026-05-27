"""Interactive prompts and display using InquirerPy + Rich."""

from __future__ import annotations

import sys
import termios
import tty
from decimal import Decimal

from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .exceptions import Cancelled
from .models import Report, Transfer  # noqa: TC001

console = Console()

_ACTION_KEYS: dict[str, str] = {
    "a": "add",
    "e": "edit",
    "r": "report",
    "s": "settle",
    "p": "participant",
    "d": "delete",
    "x": "remove_report",
    "q": "quit",
}


def _read_key() -> str:
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1).lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _check_cancel(value: str) -> str:
    if value.strip().lower() == "x":
        raise Cancelled
    return value


def prompt_text(message: str, **kwargs: object) -> str:
    result = inquirer.text(
        message=f"{message} (x to cancel)",
        **kwargs,
    ).execute()
    return _check_cancel(result)


def prompt_select(
    message: str, choices: list, cancel: bool = True, **kwargs: object
) -> str:  # noqa: FBT001, FBT002
    if cancel:
        choices = [*choices, {"name": "(X) Cancel", "value": "__cancel__"}]
    prompt = inquirer.select(message=message, choices=choices, **kwargs)
    if cancel:

        @prompt.register_kb("x")
        def _cancel(event: object) -> None:
            prompt.status["answered"] = True
            prompt.status["result"] = ["(X) Cancel"]
            event.app.exit(result="__cancel__")

    result = prompt.execute()
    if result == "__cancel__":
        raise Cancelled
    return result


def prompt_checkbox(message: str, choices: list[str], **kwargs: object) -> list[str]:
    enabled_choices = [{"name": c, "value": c, "enabled": True} for c in choices]
    enabled_choices.append({"name": "(X) Cancel", "value": "__cancel__"})
    prompt = inquirer.checkbox(
        message=message,
        choices=enabled_choices,
        instruction="(use SPACE to toggle, ENTER to confirm, x to cancel)",
        **kwargs,
    )

    @prompt.register_kb("x")
    def _cancel(event: object) -> None:
        prompt.status["answered"] = True
        prompt.status["result"] = ["(X) Cancel"]
        event.app.exit(result=["__cancel__"])

    result = prompt.execute()
    if "__cancel__" in result:
        raise Cancelled
    return result


def prompt_report_selection(
    report_slugs: list[str],
) -> tuple[str, str | None]:
    choices = ["New report", *report_slugs]
    if report_slugs:
        choices.append({"name": "Delete a report", "value": "__delete__"})
    result = prompt_select("Select a report:", choices, cancel=False)
    if result == "New report":
        return ("new", None)
    if result == "__delete__":
        return ("delete", None)
    return ("existing", result)


def prompt_action() -> str:
    console.print()
    console.print("[bold]What would you like to do?[/bold]")
    console.print("  [cyan](A)[/cyan] Add spending")
    console.print("  [cyan](E)[/cyan] Edit spending")
    console.print("  [cyan](R)[/cyan] View report")
    console.print("  [cyan](S)[/cyan] Settle up")
    console.print("  [cyan](P)[/cyan] Add participant")
    console.print("  [cyan](D)[/cyan] Delete spending")
    console.print("  [cyan](X)[/cyan] Delete report")
    console.print("  [cyan](Q)[/cyan] Quit  [dim](or Ctrl+C)[/dim]")
    console.print()

    while True:
        key = _read_key()
        if key in _ACTION_KEYS:
            action = _ACTION_KEYS[key]
            console.print(f"[dim]> {action}[/dim]")
            return action


def display_report(report: Report) -> None:
    if not report.spendings:
        print_info("No spendings yet.")
        return

    table = Table(title=f"Report: {report.name}", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Description")
    table.add_column("Amount", justify="right")
    table.add_column("Paid by")
    table.add_column("Split among")
    table.add_column("Each owes", justify="right")

    for i, s in enumerate(report.spendings, 1):
        if s.custom_amounts:
            shares = ", ".join(f"{p}: {a}" for p, a in s.custom_amounts.items())
        else:
            share = (s.amount / len(s.participants)).quantize(Decimal("0.01"))
            shares = str(share)

        table.add_row(
            str(i),
            s.description,
            f"{s.amount:.2f}",
            s.paid_by,
            ", ".join(s.participants),
            shares,
        )

    console.print(table)


def display_settlement(
    transfers: list[Transfer], balances: dict[str, Decimal], report: Report
) -> None:
    total_spent = sum(s.amount for s in report.spendings)

    spent_per_person: dict[str, Decimal] = {p: Decimal("0") for p in report.participants}
    for s in report.spendings:
        spent_per_person[s.paid_by] += s.amount

    console.print()
    summary = Table(title="Spending Summary", show_lines=False)
    summary.add_column("Participant")
    summary.add_column("Total paid", justify="right")
    for p in report.participants:
        summary.add_row(p, f"{spent_per_person[p]:.2f}")
    summary.add_section()
    summary.add_row("[bold]Total[/bold]", f"[bold]{total_spent:.2f}[/bold]")
    console.print(summary)

    if not transfers:
        console.print(
            Panel("Everyone is settled up!", style="green", title="Settlement")
        )
        return

    lines = []
    for t in transfers:
        lines.append(f"  {t.from_person} -> {t.to_person}: {t.amount:.2f}")

    settled = [p for p, b in balances.items() if b == 0]
    if settled:
        lines.append("")
        for p in settled:
            lines.append(f"  {p}: settled (no action needed)")

    console.print(Panel("\n".join(lines), title="Settlement", style="cyan"))


def print_info(message: str) -> None:
    console.print(f"[dim]{message}[/dim]")


def print_success(message: str) -> None:
    console.print(f"[green]{message}[/green]")


def print_error(message: str) -> None:
    console.print(f"[red]{message}[/red]")
