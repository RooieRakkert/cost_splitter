# Cost Splitter

Interactive CLI tool for splitting shared expenses among a group of people.

## Features

- **Multiple reports** — track separate events (holiday, dinner, office lunches)
- **Equal, custom, or percentage splits** — split evenly, by exact amounts, or by percentage
- **Debt simplification** — minimizes the number of transfers needed to settle up
- **Spending summary** — see total expenditure and per-person breakdown
- **Interactive menus** — arrow keys and keyboard shortcuts throughout
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

1. **Select, create, or delete a report** — on startup, pick an existing report, create a new one, or delete one
2. **Main menu** — press a key to choose an action:
   - `A` — Add a spending
   - `E` — Edit an existing spending
   - `R` — View the full spending report as a table
   - `S` — Settle up (spending summary + simplified transfers)
   - `P` — Add a new participant
   - `D` — Delete a spending
   - `X` — Delete the entire report
   - `Q` — Quit
3. **Cancel anytime** — type `x` in text prompts or press `x` in select/checkbox menus to go back
4. **Exit anytime** — press `Ctrl+C` from anywhere to exit cleanly

## Running tests

```bash
pip install -e ".[dev]"
pytest src/cost_splitter/tests/ -v
```
