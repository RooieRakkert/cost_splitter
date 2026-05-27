"""JSON file-based storage for cost split reports."""

from __future__ import annotations

from pathlib import Path

from .models import Report


class ReportStorage:
    def __init__(self, data_dir: Path | None = None) -> None:
        self._dir = data_dir or Path.cwd() / "reports"
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, slug: str) -> Path:
        return self._dir / f"{slug}.json"

    def save(self, report: Report) -> None:
        self._path(report.slug).write_text(report.model_dump_json(indent=2))

    def load(self, slug: str) -> Report:
        p = self._path(slug)
        if not p.exists():
            raise FileNotFoundError(f"Report '{slug}' not found")
        return Report.model_validate_json(p.read_text())

    def list_reports(self) -> list[str]:
        return sorted(p.stem for p in self._dir.glob("*.json"))

    def delete(self, slug: str) -> None:
        p = self._path(slug)
        if not p.exists():
            raise FileNotFoundError(f"Report '{slug}' not found")
        p.unlink()
