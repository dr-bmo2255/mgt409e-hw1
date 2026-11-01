#!/usr/bin/env python3
"""Build a one-page HTML income-statement report from output JSON files."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render January income statement HTML from output JSON."
    )
    parser.add_argument(
        "--json-dir",
        default="output",
        help="Directory containing income_statement, reconciliation, and judgment JSON.",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output HTML path, e.g. output/income_statement.html",
    )
    return parser.parse_args()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def money(value) -> str:
    return f"${float(value):,.2f}"


def classify_excluded(row: dict) -> str:
    text = f"{row.get('id', '')} {row.get('resolution', '')}".lower()
    if "personal" in text or "owner_draw" in text:
        return "personal"
    return "business"


def rows_html(rows: list[dict], kind: str) -> str:
    if not rows:
        return f"<p class='empty'>No {html.escape(kind)} rows were excluded.</p>"
    items = []
    for row in rows:
        amount = money(row.get("amount_used_in_income_statement") or 0)
        seen = row.get("amounts_seen") or {}
        seen_bits = ", ".join(
            f"{html.escape(str(name))}: {money(val)}" for name, val in seen.items()
        )
        items.append(
            f"""
            <article class="ticket">
              <h3>{html.escape(str(row.get('id', '')))}</h3>
              <p class="meta">Booked amount: <strong>{amount}</strong></p>
              <p class="meta">Amounts seen: {seen_bits or '—'}</p>
              <p>{html.escape(str(row.get('resolution', '')))}</p>
            </article>
            """
        )
    return "\n".join(items)


def expense_rows_html(lines: list[dict]) -> str:
    body = []
    for line in lines:
        sources = ", ".join(html.escape(str(s)) for s in (line.get("sources") or []))
        body.append(
            f"""
            <tr>
              <td>{html.escape(str(line.get('label', '')))}</td>
              <td>{html.escape(str(line.get('category', '')))}</td>
              <td class="num">{money(line.get('amount_usd'))}</td>
              <td class="sources">{sources}</td>
            </tr>
            """
        )
    return "\n".join(body)


def judgment_html(calls: list[dict]) -> str:
    cards = []
    for call in calls:
        evidence = "".join(
            f"<li>{html.escape(str(item))}</li>"
            for item in (call.get("evidence_for") or [])
        )
        cards.append(
            f"""
            <article class="ticket brass">
              <h3>{html.escape(str(call.get('transaction_id', '')))}</h3>
              <p class="meta">Included: <strong>{html.escape(str(call.get('included_in_income_statement', '')))}</strong>
              · Amount used: <strong>{money(call.get('amount_used_in_income_statement'))}</strong>
              · Confidence: <strong>{html.escape(str(call.get('confidence', '')))}</strong></p>
              <p class="meta">Evidence</p>
              <ul>{evidence}</ul>
            </article>
            """
        )
    return "\n".join(cards)


def build_html(statement: dict, recon: list, judgments: list) -> str:
    excluded = [
        row
        for row in recon
        if str(row.get("included_in_income_statement", "")).strip().lower() == "no"
    ]
    personal = [row for row in excluded if classify_excluded(row) == "personal"]
    business = [row for row in excluded if classify_excluded(row) == "business"]
    period = html.escape(str(statement.get("period", "")))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Spoke &amp; Wrench · January 2026 Income Statement</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,700;1,500&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --oak: #5c3a1e;
      --oak-dark: #2b170c;
      --brass: #c4a35a;
      --brass-bright: #e6c87a;
      --lamp: #1f6b45;
      --lamp-glass: #3cb371;
      --leather: #3a1f18;
      --paper: #f3e6c4;
      --ink: #1a120c;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: "Cormorant Garamond", Georgia, serif;
      background:
        radial-gradient(ellipse at 50% 0%, rgba(60, 179, 113, 0.28), transparent 42%),
        linear-gradient(180deg, #1a0f08 0%, var(--oak-dark) 28%, #4a2c16 100%);
      min-height: 100vh;
    }}
    .shade {{
      height: 72px;
      background: linear-gradient(180deg, #145c38, var(--lamp));
      box-shadow: 0 24px 40px rgba(60, 179, 113, 0.35);
      border-bottom: 8px solid var(--brass);
    }}
    main {{
      width: min(980px, calc(100% - 2rem));
      margin: -24px auto 3rem;
      background: var(--paper);
      border: 10px solid var(--oak);
      outline: 3px solid var(--brass);
      box-shadow: 0 24px 50px rgba(0,0,0,0.45);
      padding: 2rem 2.2rem 2.6rem;
    }}
    header h1 {{
      margin: 0;
      font-size: clamp(2.2rem, 5vw, 3.4rem);
      letter-spacing: 0.04em;
    }}
    .brass-rule {{
      height: 4px;
      background: linear-gradient(90deg, transparent, var(--brass), var(--brass-bright), var(--brass), transparent);
      margin: 0.85rem 0 1.1rem;
    }}
    .lede {{
      margin: 0;
      font-size: 1.2rem;
    }}
    h2 {{
      margin: 2rem 0 0.7rem;
      color: var(--leather);
      border-bottom: 2px solid var(--brass);
      padding-bottom: 0.25rem;
    }}
    .totals {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.75rem;
    }}
    .totals div {{
      background: var(--leather);
      color: var(--paper);
      padding: 0.9rem 1rem;
      border-top: 4px solid var(--brass);
    }}
    .totals span {{
      display: block;
      font-family: "IBM Plex Mono", monospace;
      font-size: 0.78rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--brass-bright);
    }}
    .totals strong {{
      font-size: 1.55rem;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 1.02rem;
    }}
    th, td {{
      text-align: left;
      padding: 0.45rem 0.4rem;
      border-bottom: 1px solid rgba(92, 58, 30, 0.25);
      vertical-align: top;
    }}
    th {{
      font-family: "IBM Plex Mono", monospace;
      font-size: 0.75rem;
      text-transform: uppercase;
      color: var(--oak);
    }}
    .num {{
      font-family: "IBM Plex Mono", monospace;
      white-space: nowrap;
      text-align: right;
    }}
    .sources {{ font-size: 0.92rem; color: #4a3424; }}
    .ticket {{
      background: #efe0b8;
      border-left: 6px solid var(--lamp);
      padding: 0.8rem 1rem;
      margin: 0.65rem 0;
    }}
    .ticket.brass {{ border-left-color: var(--brass); }}
    .ticket h3 {{ margin: 0 0 0.3rem; }}
    .meta {{ margin: 0.2rem 0; }}
    ul {{ margin: 0.3rem 0 0 1.1rem; }}
    footer {{
      margin-top: 2rem;
      font-size: 0.95rem;
      color: #5a4030;
    }}
    @media (max-width: 720px) {{
      .totals {{ grid-template-columns: 1fr; }}
      main {{ padding: 1.2rem; }}
    }}
  </style>
</head>
<body>
  <div class="shade"></div>
  <main>
    <header>
      <h1>Spoke &amp; Wrench Bicycle Repair</h1>
      <div class="brass-rule"></div>
      <p class="lede">January income statement · Period {period} · 142 Crown Street, New Haven</p>
    </header>

    <section>
      <h2>January income statement</h2>
      <div class="totals">
        <div><span>Revenue</span><strong>{money(statement.get("revenue_usd"))}</strong></div>
        <div><span>Total expenses</span><strong>{money(statement.get("total_expenses_usd"))}</strong></div>
        <div><span>Net income</span><strong>{money(statement.get("net_income_usd"))}</strong></div>
      </div>
      <table>
        <thead>
          <tr><th>Expense</th><th>Category</th><th class="num">Amount</th><th>Sources</th></tr>
        </thead>
        <tbody>
          {expense_rows_html(statement.get("expense_lines") or [])}
        </tbody>
      </table>
    </section>

    <section>
      <h2>Excluded personal rows</h2>
      {rows_html(personal, "personal")}
    </section>

    <section>
      <h2>Excluded business rows</h2>
      {rows_html(business, "business")}
    </section>

    <section>
      <h2>Judgment calls</h2>
      {judgment_html(judgments)}
    </section>

    <footer>
      Figures are copied from output JSON files. Totals are not recalculated on this page.
    </footer>
  </main>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    json_dir = Path(args.json_dir).resolve()
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    statement = load_json(json_dir / "income_statement_jan2026.json")
    recon = load_json(json_dir / "reconciliation_log.json")
    judgments = load_json(json_dir / "judgment_calls.json")

    out_path.write_text(build_html(statement, recon, judgments), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(
        "JSON totals used as-is: "
        f"revenue={statement.get('revenue_usd')} "
        f"expenses={statement.get('total_expenses_usd')} "
        f"net={statement.get('net_income_usd')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
