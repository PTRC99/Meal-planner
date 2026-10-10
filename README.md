# TablePlan

A runnable Python + browser meal planner with no third-party dependencies.

## Run

Install Python 3.10 or newer, unzip this folder, then run from this folder:

```sh
python server.py
```

Open http://localhost:8000. On systems using `python3`, substitute that command.

## Features

- Choose Keto, Vegan, High Protein, or Affordable.
- Set 1–20 people and 1–31 days.
- Enter a ZIP code or street address.
- Generate one dinner per day, scaled ingredients, an aggregated shopping checklist, and recipe directions.
- Print the plan. Responsive layout works on mobile.
- Eight starter recipes (two per category); longer plans repeat them.

## Grocery availability: demo versus live

Out of the box, three **fictional** stores illustrate the shopping interface. They are not actual nearby stores. No inventory, distance or price is claimed in demo mode.

Live nearby stores and item availability require an authorized grocery-data service. The included server has an adapter contract, not an implementation of a commercial grocery API. Configure your own HTTPS service with `GROCERY_PROVIDER_URL` and optionally `GROCERY_PROVIDER_TOKEN`; keep tokens on the server. No API keys are included.

The app POSTs this JSON to that endpoint:

```json
{"location":"30101","limit":3,"ingredients":[{"name":"Chicken breast","quantity":800,"unit":"g"}]}
```

Your adapter must geocode the location, find grocery stores, sort by distance, and perform inventory lookups at the closest three stores. Return:

```json
{"stores":[{"name":"Actual store name","address":"Street address","distanceKm":1.2,"checkedAt":"2026-10-10T13:00:00Z","items":[{"name":"Chicken breast","availability":"Available","price":7.99,"currency":"USD"}]}]}
```

`price` is optional and represents a package price, not the full recipe cost. Use `Unavailable` or `Not verified` rather than inventing stock. Return all requested ingredients for each store, even unavailable ones. If fewer than three stores exist, return those found. The app orders provider results by distance and displays at most three; correctness and coverage depend on the adapter. Live lookup errors show an error, without silently switching to demo.

## Tests

```sh
python -m unittest -v
```

This is a local prototype. Before public deployment, use a production web server, rate limits, request timeouts, appropriate privacy controls for locations, and a reviewed provider integration. Keto and high-protein tags reflect ingredient choices; nutrition macros are not calculated. Affordable means low-cost ingredient choices, not a verified lowest-price guarantee. Ingredients are purchase targets, not exact package counts. Directions use package instructions for rice and account for safe poultry temperatures; scale cookware and cook in batches for larger groups.
