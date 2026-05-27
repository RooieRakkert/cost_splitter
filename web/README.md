# Cost Splitter — Web App

Static single-page web application for the Cost Splitter. Runs entirely in the browser with no server or build step required.

## Architecture

```
web/
├── index.html      # App shell (all views as show/hide sections)
├── style.css       # Responsive styling, no framework
├── app.js          # UI rendering, event handling, state management
├── calculator.js   # Balance calculation + debt simplification (ported from Python)
└── storage.js      # localStorage wrapper for report persistence
```

## Data Storage

Reports are stored in `localStorage` with the key prefix `cost_splitter:`:

```
cost_splitter:holiday-trip → { name, slug, participants, spendings, createdAt }
```

Each spending within a report:

```json
{
  "description": "Dinner",
  "amount": 60.00,
  "paidBy": "Bouke",
  "participants": ["Bouke", "Jan", "Karel"],
  "customAmounts": null,
  "createdAt": "2026-05-27T12:00:00.000Z"
}
```

When `customAmounts` is not null, it's a map of participant to amount (used for both custom and percentage splits — percentages are converted to amounts at entry time).

## Running Locally

Since ES modules require a server (can't use `file://`), use any local HTTP server:

```bash
cd web
python3 -m http.server 8000
```

Then open http://localhost:8000

## Calculator Parity

`calculator.js` is a direct port of `src/cost_splitter/calculator.py`:

- `calculateBalances(report)` — net balance per participant (positive = owed, negative = owes)
- `calculateSettlement(report)` — greedy debt simplification, minimizes transfer count
- Rounding: `Math.round(x * 100) / 100` (equivalent to Python's `Decimal.quantize(0.01, ROUND_HALF_UP)`)

## Deployment

Hosted on GitHub Pages from the `web/` directory. Enable in repo settings:
Settings → Pages → Source: branch `main`, folder `/web`.
