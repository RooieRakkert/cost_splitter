"""Tests for cost_splitter JSON storage."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path  # noqa: TC003

import pytest

from ..models import Report, Spending
from ..storage import ReportStorage


@pytest.fixture()
def storage(tmp_path: Path) -> ReportStorage:
    return ReportStorage(data_dir=tmp_path)


@pytest.fixture()
def sample_report() -> Report:
    r = Report(name="Holiday Trip", participants=["Bouke", "Jan", "Karel"])
    r.spendings.append(
        Spending(
            description="Dinner",
            amount=Decimal("60.00"),
            paid_by="Bouke",
            participants=["Bouke", "Jan", "Karel"],
        )
    )
    return r


class TestReportStorage:
    def test_save_and_load(self, storage: ReportStorage, sample_report: Report) -> None:
        storage.save(sample_report)
        loaded = storage.load("holiday-trip")
        assert loaded.name == "Holiday Trip"
        assert loaded.participants == ["Bouke", "Jan", "Karel"]
        assert len(loaded.spendings) == 1
        assert loaded.spendings[0].amount == Decimal("60.00")

    def test_save_creates_json_file(
        self, storage: ReportStorage, sample_report: Report, tmp_path: Path
    ) -> None:
        storage.save(sample_report)
        assert (tmp_path / "holiday-trip.json").exists()

    def test_load_nonexistent_raises(self, storage: ReportStorage) -> None:
        with pytest.raises(FileNotFoundError):
            storage.load("nonexistent")

    def test_list_empty(self, storage: ReportStorage) -> None:
        assert storage.list_reports() == []

    def test_list_reports(self, storage: ReportStorage) -> None:
        r1 = Report(name="Trip A", participants=["A", "B"])
        r2 = Report(name="Trip B", participants=["C", "D"])
        storage.save(r1)
        storage.save(r2)
        names = sorted(storage.list_reports())
        assert names == ["trip-a", "trip-b"]

    def test_delete_report(self, storage: ReportStorage, sample_report: Report) -> None:
        storage.save(sample_report)
        storage.delete("holiday-trip")
        assert storage.list_reports() == []

    def test_delete_nonexistent_raises(self, storage: ReportStorage) -> None:
        with pytest.raises(FileNotFoundError):
            storage.delete("nonexistent")

    def test_overwrite_existing(
        self, storage: ReportStorage, sample_report: Report
    ) -> None:
        storage.save(sample_report)
        sample_report.spendings.append(
            Spending(
                description="Taxi",
                amount=Decimal("15.00"),
                paid_by="Jan",
                participants=["Bouke", "Jan"],
            )
        )
        storage.save(sample_report)
        loaded = storage.load("holiday-trip")
        assert len(loaded.spendings) == 2

    def test_load_all(self, storage: ReportStorage) -> None:
        r1 = Report(name="Trip A", participants=["A", "B"])
        r2 = Report(name="Trip B", participants=["C", "D"])
        storage.save(r1)
        storage.save(r2)
        reports = storage.load_all()
        assert len(reports) == 2
        names = sorted(r.name for r in reports)
        assert names == ["Trip A", "Trip B"]
