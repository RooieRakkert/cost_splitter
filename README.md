# Cost Splitter

Interactive CLI tool for splitting shared expenses among a group of people.

## Features

- **Multiple reports** — track separate events (holiday, dinner, office lunches)
- **Equal or custom splits** — split evenly or assign custom amounts per person
- **Debt simplification** — minimizes the number of transfers needed to settle up
- **Interactive menus** — arrow keys, keyboard shortcuts, and checkbox selection
- **JSON storage** — reports saved as human-readable JSON in `./reports/`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
python -m cost_splitter
```

Or via the installed command:

```bash
cost-splitter
```

## How it works

1. **Select or create a report** — on startup, pick an existing report or create a new one with participants
2. **Main menu** — press a key to choose an action:
   - `A` — Add a spending (description, amount, who paid, who participates, equal/custom split)
   - `R` — View the full spending report as a table
   - `S` — Settle up (shows simplified transfers)
   - `D` — Delete a spending
   - `Q` — Quit
3. **Cancel anytime** — type `x` in text prompts or select `(X) Cancel` in menus to go back

## Running tests

```bash
pip install -e ".[dev]"
pytest src/cost_splitter/tests/ -v
```
