"""Tests for the interactive cost splitter app logic."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path  # noqa: TC003
from unittest.mock import MagicMock, patch

import pytest

from .. import ui as _ui_module
from ..app import CostSplitterApp
from ..models import Report, Spending
from ..storage import ReportStorage

_UI = _ui_module.__name__


@pytest.fixture()
def storage(tmp_path: Path) -> ReportStorage:
    return ReportStorage(data_dir=tmp_path)


@pytest.fixture()
def app(storage: ReportStorage) -> CostSplitterApp:
    return CostSplitterApp(storage=storage)


@pytest.fixture()
def report_with_spendings(storage: ReportStorage) -> Report:
    r = Report(name="Holiday", participants=["Bouke", "Jan", "Karel"])
    r.spendings.append(
        Spending(
            description="Dinner",
            amount=Decimal("60.00"),
            paid_by="Bouke",
            participants=["Bouke", "Jan", "Karel"],
        )
    )
    storage.save(r)
    return r


class TestCreateReport:
    @patch(f"{_UI}.prompt_text")
    def test_create_new_report(
        self, mock_text: MagicMock, app: CostSplitterApp
    ) -> None:
        mock_text.side_effect = ["Beach Trip", "Bouke, Jan, Karel"]
        report = app.create_report()
        assert report.name == "Beach Trip"
        assert report.participants == ["Bouke", "Jan", "Karel"]
        loaded = app.storage.load("beach-trip")
        assert loaded.name == "Beach Trip"

    @patch(f"{_UI}.prompt_text")
    def test_create_report_trims_whitespace(
        self, mock_text: MagicMock, app: CostSplitterApp
    ) -> None:
        mock_text.side_effect = ["Trip", " Bouke , Jan "]
        report = app.create_report()
        assert report.participants == ["Bouke", "Jan"]


class TestAddSpending:
    @patch(f"{_UI}.prompt_select")
    @patch(f"{_UI}.prompt_checkbox")
    @patch(f"{_UI}.prompt_text")
    def test_add_equal_spending(
        self,
        mock_text: MagicMock,
        mock_checkbox: MagicMock,
        mock_select: MagicMock,
        app: CostSplitterApp,
        report_with_spendings: Report,
    ) -> None:
        mock_text.side_effect = ["Taxi", "15.00"]
        mock_select.side_effect = ["Jan", "Equal"]
        mock_checkbox.return_value = ["Bouke", "Jan"]

        app.add_spending(report_with_spendings)

        loaded = app.storage.load("holiday")
        assert len(loaded.spendings) == 2
        new_spending = loaded.spendings[1]
        assert new_spending.description == "Taxi"
        assert new_spending.amount == Decimal("15.00")
        assert new_spending.paid_by == "Jan"
        assert new_spending.participants == ["Bouke", "Jan"]
        assert new_spending.custom_amounts is None

    @patch(f"{_UI}.prompt_select")
    @patch(f"{_UI}.prompt_checkbox")
    @patch(f"{_UI}.prompt_text")
    def test_add_custom_spending(
        self,
        mock_text: MagicMock,
        mock_checkbox: MagicMock,
        mock_select: MagicMock,
        app: CostSplitterApp,
        report_with_spendings: Report,
    ) -> None:
        mock_text.side_effect = ["Hotel", "100.00", "60.00", "40.00"]
        mock_select.side_effect = ["Bouke", "Custom"]
        mock_checkbox.return_value = ["Bouke", "Jan"]

        app.add_spending(report_with_spendings)

        loaded = app.storage.load("holiday")
        new_spending = loaded.spendings[1]
        assert new_spending.custom_amounts == {
            "Bouke": Decimal("60.00"),
            "Jan": Decimal("40.00"),
        }


class TestDeleteSpending:
    @patch(f"{_UI}.prompt_select")
    def test_delete_spending(
        self,
        mock_select: MagicMock,
        app: CostSplitterApp,
        report_with_spendings: Report,
    ) -> None:
        mock_select.return_value = 0
        app.delete_spending(report_with_spendings)
        loaded = app.storage.load("holiday")
        assert len(loaded.spendings) == 0

    @patch(f"{_UI}.print_info")
    def test_delete_spending_empty_report(
        self,
        mock_print: MagicMock,
        app: CostSplitterApp,
        storage: ReportStorage,
    ) -> None:
        r = Report(name="Empty", participants=["A"])
        storage.save(r)
        app.delete_spending(r)
        mock_print.assert_called()


class TestViewReport:
    @patch(f"{_UI}.display_report")
    def test_view_report_calls_display(
        self,
        mock_display: MagicMock,
        app: CostSplitterApp,
        report_with_spendings: Report,
    ) -> None:
        app.view_report(report_with_spendings)
        mock_display.assert_called_once_with(report_with_spendings)


class TestSettle:
    @patch(f"{_UI}.display_settlement")
    def test_settle_calls_display(
        self,
        mock_display: MagicMock,
        app: CostSplitterApp,
        report_with_spendings: Report,
    ) -> None:
        app.settle(report_with_spendings)
        mock_display.assert_called_once()
        transfers = mock_display.call_args[0][0]
        assert len(transfers) == 2
        total = sum(t.amount for t in transfers)
        assert total == Decimal("40.00")


class TestMainLoop:
    @patch(f"{_UI}.prompt_action")
    @patch(f"{_UI}.prompt_report_selection")
    def test_quit_exits(
        self,
        mock_report_sel: MagicMock,
        mock_action: MagicMock,
        app: CostSplitterApp,
        report_with_spendings: Report,  # noqa: ARG002
    ) -> None:
        mock_report_sel.return_value = ("existing", "holiday")
        mock_action.return_value = "quit"
        app.run()

    @patch(f"{_UI}.prompt_action")
    @patch(f"{_UI}.prompt_report_selection")
    @patch(f"{_UI}.display_report")
    def test_view_then_quit(
        self,
        mock_display: MagicMock,
        mock_report_sel: MagicMock,
        mock_action: MagicMock,
        app: CostSplitterApp,
        report_with_spendings: Report,  # noqa: ARG002
    ) -> None:
        mock_report_sel.return_value = ("existing", "holiday")
        mock_action.side_effect = ["report", "quit"]
        app.run()
        mock_display.assert_called_once()
