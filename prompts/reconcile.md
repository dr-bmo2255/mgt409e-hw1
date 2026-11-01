You reconcile January 2026 financial documents for **Spoke & Wrench Bicycle Repair** before building the income statement.

You receive:
1. Structured JSON from Problems 2–4 (receipts, bank transactions, credit card charges)
2. Supporting text from emails and PDFs in the document pack

Your job is to produce **one reconciled row per decision**, not one row per raw extracted line. Combine duplicate appearances of the same purchase across receipt + card + bank so it is only booked once. Split or exclude items that must not appear in January revenue or expenses.

Return **one JSON object** with a single key `reconciliation` whose value is an array of row objects.

Each row must include:

- `id` — short slug (e.g. `park_tool_card_vs_receipt`)
- `sources` — list of document filenames used (PDFs, emails, or JSON files such as `output/receipts.json`)
- `amounts_seen` — object mapping each source filename to the dollar amount seen in that source (numbers, not strings)
- `included_in_income_statement` — `yes` or `no`
- `amount_used_in_income_statement` — final dollar amount to book after reconciliation; use `0` if excluded
- `resolution` — plain English explaining how documents were matched and how the final amount was chosen

Rules:

1. **Do not invent values.** Every amount in `amounts_seen` must come from the provided JSON or document text.
2. **Do not double-count** the same expense or revenue when it appears on a receipt and a card line, or on a card and a bank payment for the same purchase.
3. **Separate orders stay separate** — e.g. New Haven Bike Parts $742.18 bank check vs $218.40 card invoice are different purchases.
4. **Partial receipts** — when a receipt total is less than the matching card charge, explain why and book the correct total once (see Park Tool notes).
5. **Personal items** — exclude from the income statement (`included_in_income_statement: no`, `amount_used_in_income_statement: 0`) when owner notes or classification show they are not shop revenue/expense.
6. **Mixed deposits** — when owner notes say part of a bank deposit is personal, split into the business portion only for revenue.
7. **Future work / not January** — quotes and emails about March fleet work are not January revenue (`amount_used: 0`).
8. **IOUs / not yet collected** — do not book as January revenue if not received in bank.
9. **Judgment items** — for debatable items (e.g. REI charge), include a row with the amounts seen and note in `resolution` that classification is pending owner decision; use `included_in_income_statement: no` and `amount_used_in_income_statement: 0` until confirmed.
10. Reconcile at minimum these known cases when present in the data:
    - Park Tool receipt vs card vs bank vendor portal
    - Speedy Courier receipt vs card (count once)
    - Home Depot receipt vs card
    - New Haven Bike Parts check vs separate card invoice
    - Amazon headphones receipt vs card (personal)
    - eBay repair stand receipt vs card
    - Mixed $560 Square deposit (owner memo personal portion)
    - Hartford Mutual quote vs email (not January revenue)
    - Mike Smith IOU (not yet in bank)
    - REI card charge (pending owner classification)

Respond with valid JSON only — no markdown fences or extra commentary.
