"""Entry point for cost splitter CLI."""

from .app import CostSplitterApp


def main() -> None:
    app = CostSplitterApp()
    app.run()


if __name__ == "__main__":
    main()
