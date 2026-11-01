#!/usr/bin/env python3
"""Build the demo front page (index.html) from the JSON files in output/.

The submitted pages, output/income_statement.html and output/pipeline.html, are not changed.
Run with: python build_demo.py
"""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"

# Student's final decisions, as recorded under Problem 6 in AI_prompts.md.
JUDGMENT_REASONS = {
    "mixed_square_deposit_personal_portion": "Included at $465, the business portion of the $560 deposit.",
    "hartford_mutual_march_quote": "Not included for January. Contract only, with no service yet. Revisit next month.",
    "park_tool_receipt_vs_card": "Included at $127.40. The spanner shipped 1/12 and is presumed received by month-end. The $344.55 Park Tool debit stays a separate row.",
}

TRICKY_ROWS = [
    ("mixed_square_deposit_personal_portion", "A deposit that was partly personal"),
    ("park_tool_receipt_vs_card", "A receipt smaller than the card charge"),
    ("nhbp_restocks_check", "Two orders from one vendor"),
    ("speedy_courier_receipt_card", "One purchase in two documents"),
    ("amazon_headphones_personal", "A personal purchase on the card"),
    ("hartford_mutual_march_quote", "A big quote that isn't January revenue"),
    ("mike_smith_iou", "Money owed but not collected"),
]

NAMES = {
    "Nhbp": "NH Bike Parts",
    "Rei": "REI",
    "Ebay": "eBay",
    "Eversource": "Eversource",
    "State farm": "State Farm",
    "Park tool": "Park Tool",
    "Home depot": "Home Depot",
    "Speedy courier": "Speedy Courier",
    "Yale printing": "Yale Printing",
    "Shell": "Shell",
    "Amazon web services": "Amazon Web Services",
    "Hartford mutual march": "Hartford Mutual March",
    "Mixed square": "Mixed Square",
}


def load(name: str):
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def money(value) -> str:
    return f"${float(value):,.2f}"


def esc(value) -> str:
    return html.escape(str(value))


def pretty(label: str) -> str:
    text = label.replace("_", " ").capitalize()
    for old, new in NAMES.items():
        text = text.replace(old, new)
    return text


def revenue_rows(statement: dict, recon: list, bank: list) -> list[dict]:
    expense_ids = {line["label"].replace(" ", "_") for line in statement["expense_lines"]}
    credits = [row for row in bank if row.get("direction") == "credit"]
    rows = []
    for row in recon:
        if row["included_in_income_statement"] != "yes" or row["id"] in expense_ids:
            continue
        deposit = row["amounts_seen"]["bank_transactions.json"]
        match = next(c for c in credits if float(c["amount_usd"]) == float(deposit))
        rows.append(
            {
                "date": match["date"],
                "description": match["description"].split("—", 1)[-1].strip(),
                "deposit": deposit,
                "booked": row["amount_used_in_income_statement"],
            }
        )
    rows.sort(key=lambda r: r["date"])
    total = round(sum(float(r["booked"]) for r in rows), 2)
    if total != round(float(statement["revenue_usd"]), 2):
        raise ValueError(f"Revenue rows total {total}, statement says {statement['revenue_usd']}")
    return rows


def build(statement: dict, recon: list, judgments: list, bank: list) -> str:
    by_id = {row["id"]: row for row in recon}

    revenue_html = "".join(
        f"<tr><td>{esc(r['date'])}</td><td>{esc(r['description'])}</td>"
        f"<td class='num'>{money(r['deposit'])}</td><td class='num'>{money(r['booked'])}</td></tr>"
        for r in revenue_rows(statement, recon, bank)
    )

    expense_html = "".join(
        f"<tr><td>{esc(pretty(line['label']))}</td><td>{esc(line['category'].replace('_', ' '))}</td>"
        f"<td class='num'>{money(line['amount_usd'])}</td></tr>"
        for line in statement["expense_lines"]
    )

    tricky_html = ""
    for row_id, title in TRICKY_ROWS:
        row = by_id[row_id]
        seen = " · ".join(f"{esc(k)}: {money(v)}" for k, v in row["amounts_seen"].items())
        tricky_html += (
            f"<article class='ticket'><h3>{esc(title)}</h3>"
            f"<p class='booked'>Booked: {money(row['amount_used_in_income_statement'])}</p>"
            f"<p>{esc(row['resolution'])}</p><p class='seen'>Amounts seen: {seen}</p></article>"
        )

    judgment_html = ""
    for call in judgments:
        transaction = call["transaction_id"]
        judgment_html += (
            f"<article class='ticket brass'><h3>{esc(pretty(transaction))}</h3>"
            f"<p class='booked'>{money(call['amount_used_in_income_statement'])} · {esc(call['confidence'])} confidence</p>"
            f"<p>{esc(JUDGMENT_REASONS[transaction])}</p></article>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Spoke &amp; Wrench Demo</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,700;1,500&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root {{ --oak: #5c3a1e; --oak-dark: #2b170c; --brass: #c4a35a; --brass-bright: #e6c87a; --lamp: #1f6b45; --leather: #3a1f18; --paper: #f3e6c4; --ink: #1a120c; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; color: var(--ink); font: 500 1.15rem/1.5 "Cormorant Garamond", Georgia, serif;
    background: radial-gradient(ellipse at 50% 0%, rgba(60,179,113,.28), transparent 42%), linear-gradient(180deg, #1a0f08, var(--oak-dark) 28%, #4a2c16); min-height: 100vh; }}
  .shade {{ height: 72px; background: linear-gradient(180deg, #145c38, var(--lamp)); box-shadow: 0 24px 40px rgba(60,179,113,.35); border-bottom: 8px solid var(--brass); }}
  main {{ width: min(980px, calc(100% - 32px)); margin: -24px auto 3rem; padding: clamp(1.1rem, 4vw, 2.4rem); background: var(--paper); border: 10px solid var(--oak); outline: 3px solid var(--brass); box-shadow: 0 24px 50px rgba(0,0,0,.45); }}
  h1 {{ margin: 0; font-size: clamp(2.1rem, 6vw, 3.3rem); line-height: 1.1; }}
  h2 {{ margin: 2.3rem 0 .6rem; color: var(--leather); font-size: 1.7rem; border-bottom: 2px solid var(--brass); padding-bottom: .25rem; }}
  h3 {{ margin: 0 0 .2rem; font-size: 1.25rem; }}
  p {{ margin: .35rem 0; }}
  .lede {{ font-size: 1.3rem; }}
  .buttons {{ display: flex; flex-wrap: wrap; gap: .7rem; margin: 1.2rem 0 0; }}
  .btn {{ padding: .6rem 1rem; color: var(--paper); background: var(--lamp); border: 1px solid var(--brass); font: 600 .8rem "IBM Plex Mono", monospace; text-decoration: none; }}
  .btn.primary {{ color: var(--ink); background: var(--brass-bright); }}
  .btn:hover {{ filter: brightness(1.12); }}
  .btn:focus-visible {{ outline: 3px solid var(--leather); outline-offset: 2px; }}
  .totals {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: .75rem; }}
  .totals div {{ padding: .9rem 1rem; color: var(--paper); background: var(--leather); border-top: 4px solid var(--brass); }}
  .totals span {{ display: block; color: var(--brass-bright); font: 600 .75rem "IBM Plex Mono", monospace; letter-spacing: .08em; text-transform: uppercase; }}
  .totals strong {{ font-size: 1.6rem; }}
  .steps {{ margin: .4rem 0 0; padding-left: 1.4rem; }}
  .steps li {{ margin: .3rem 0; }}
  .table-wrap {{ overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ padding: .4rem; text-align: left; vertical-align: top; border-bottom: 1px solid rgba(92,58,30,.25); }}
  th {{ color: var(--oak); font: 600 .72rem "IBM Plex Mono", monospace; text-transform: uppercase; }}
  th.num, td.num {{ text-align: right; white-space: nowrap; font-family: "IBM Plex Mono", monospace; font-size: .92rem; }}
  tfoot td {{ font-weight: 700; border-top: 2px solid var(--oak); border-bottom: 0; }}
  .ticket {{ margin: .7rem 0; padding: .8rem 1rem; background: #efe0b8; border-left: 6px solid var(--lamp); }}
  .ticket.brass {{ border-left-color: var(--brass); }}
  .booked {{ color: var(--oak); font: 600 .85rem "IBM Plex Mono", monospace; }}
  .seen {{ color: #4a3424; font-size: .95rem; overflow-wrap: anywhere; }}
  footer {{ margin-top: 2rem; color: #5a4030; font-size: 1rem; }}
  @media (max-width: 720px) {{ .totals {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="shade"></div>
<main>
  <header>
    <h1>Spoke &amp; Wrench Bicycle Repair</h1>
    <p class="lede">AI reads a bike shop's messy January paperwork, and Python and a human turn it into an income statement you can trace back to the documents.</p>
    <div class="buttons">
      <a class="btn primary" href="output/pipeline.html">See the workflow map</a>
      <a class="btn" href="output/income_statement.html">Open the submitted report</a>
      <a class="btn" href="https://github.com/dr-bmo2255/mgt409e-hw1">View on GitHub</a>
    </div>
  </header>

  <section>
    <h2>The result: January 2026</h2>
    <div class="totals">
      <div><span>Revenue</span><strong>{money(statement['revenue_usd'])}</strong></div>
      <div><span>Expenses</span><strong>{money(statement['total_expenses_usd'])}</strong></div>
      <div><span>Net income</span><strong>{money(statement['net_income_usd'])}</strong></div>
    </div>
  </section>

  <section>
    <h2>How it works</h2>
    <ol class="steps">
      <li><strong>Extract:</strong> an LLM turns the receipts, bank statement and card statement into structured data.</li>
      <li><strong>Reconcile:</strong> an LLM matches amounts across documents and proposes one decision for each.</li>
      <li><strong>Decide:</strong> the student makes the final call on the three hardest items.</li>
      <li><strong>Report:</strong> plain Python, with no LLM, adds up the totals and builds the page.</li>
    </ol>
  </section>

  <section>
    <h2>Where the paperwork didn't agree</h2>
    {tricky_html}
  </section>

  <section>
    <h2>The three human judgment calls</h2>
    {judgment_html}
  </section>

  <section>
    <h2>Revenue</h2>
    <div class="table-wrap"><table>
      <thead><tr><th>Date</th><th>Deposit</th><th class="num">In bank</th><th class="num">Booked</th></tr></thead>
      <tbody>{revenue_html}</tbody>
      <tfoot><tr><td colspan="3">Total revenue</td><td class="num">{money(statement['revenue_usd'])}</td></tr></tfoot>
    </table></div>
  </section>

  <section>
    <h2>Expenses</h2>
    <div class="table-wrap"><table>
      <thead><tr><th>Expense</th><th>Category</th><th class="num">Amount</th></tr></thead>
      <tbody>{expense_html}</tbody>
      <tfoot><tr><td colspan="2">Total expenses</td><td class="num">{money(statement['total_expenses_usd'])}</td></tr></tfoot>
    </table></div>
  </section>

  <footer>Class project for Yale SOM MGT 409E, AI Foundations for Managers. This page shows the saved results of one pipeline run; it doesn't call an LLM. The source PDFs and emails are kept private.</footer>
</main>
</body>
</html>
"""


def main() -> int:
    page = build(
        load("income_statement_jan2026.json"),
        load("reconciliation_log.json"),
        load("judgment_calls.json"),
        load("bank_transactions.json"),
    )
    (ROOT / "index.html").write_text(page, encoding="utf-8")
    print("Wrote index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
