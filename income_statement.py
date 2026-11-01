#!/usr/bin/env python3
"""Build the January income statement from the reconciliation log (no LLM)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PERIOD = "2026-01"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Roll included reconciliation rows into a January income statement."
    )
    parser.add_argument(
        "--json-dir",
        default="output",
        help="Directory containing reconciliation_log.json and supporting JSON.",
    )
    parser.add_argument(
        "--out-dir",
        default="output",
        help="Directory where income_statement_jan2026.json will be written.",
    )
    return parser.parse_args()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def money(value: float) -> float:
    return round(float(value), 2)


def is_included(row: dict) -> bool:
    return str(row.get("included_in_income_statement", "")).strip().lower() == "yes"


def is_revenue_row(row: dict) -> bool:
    text = f"{row.get('id', '')} {row.get('resolution', '')}".lower()
    return "revenue" in text


def label_from_id(row_id: str) -> str:
    return row_id.replace("_", " ").strip()


def category_from_text(row: dict) -> str:
    text = f"{row.get('id', '')} {row.get('resolution', '')}".lower()
    rules = (
        ("rent", "rent"),
        ("cogs", "cogs_parts"),
        ("parts", "cogs_parts"),
        ("nhbp", "cogs_parts"),
        ("insurance", "insurance"),
        ("bank fee", "bank_fees"),
        ("service fee", "bank_fees"),
        ("utility", "utilities"),
        ("utilities", "utilities"),
        ("eversource", "utilities"),
        ("comcast", "utilities"),
        ("shipping", "shipping"),
        ("courier", "shipping"),
        ("office", "office"),
        ("staples", "office"),
        ("supplies", "supplies"),
        ("home depot", "supplies"),
        ("marketing", "marketing"),
        ("printing", "marketing"),
        ("fuel", "fuel"),
        ("shell", "fuel"),
        ("software", "software"),
        ("web services", "software"),
        ("tools", "tools_equipment"),
        ("equipment", "tools_equipment"),
        ("park tool", "tools_equipment"),
        ("ebay", "tools_equipment"),
        ("rei", "tools_equipment"),
    )
    for needle, category in rules:
        if needle in text:
            return category
    return "expense"


def lookup_category(row: dict, receipts: list, bank_rows: list, card_rows: list) -> str:
    sources = set(row.get("sources") or [])
    amount = money(row.get("amount_used_in_income_statement") or 0)

    for receipt in receipts:
        if receipt.get("source_file") in sources:
            category = receipt.get("category")
            if category and category != "personal":
                return category

    for card in card_rows:
        if money(card.get("amount_usd") or 0) == amount:
            category = card.get("expense_category")
            if category:
                return category

    seen = row.get("amounts_seen") or {}
    bank_amount = seen.get("bank_transactions.json")
    if bank_amount is not None:
        for bank in bank_rows:
            if money(bank.get("amount_usd") or 0) == money(bank_amount):
                expense_type = bank.get("expense_type")
                if expense_type:
                    return expense_type

    return category_from_text(row)


def build_statement(
    recon_rows: list,
    receipts: list,
    bank_rows: list,
    card_rows: list,
) -> dict:
    revenue_usd = 0.0
    expense_lines: list[dict] = []

    for row in recon_rows:
        if not is_included(row):
            continue
        amount = money(row.get("amount_used_in_income_statement") or 0)
        if amount == 0:
            continue

        if is_revenue_row(row):
            revenue_usd += amount
            continue

        expense_lines.append(
            {
                "label": label_from_id(row.get("id", "expense")),
                "amount_usd": amount,
                "category": lookup_category(row, receipts, bank_rows, card_rows),
                "sources": list(row.get("sources") or []),
            }
        )

    revenue_usd = money(revenue_usd)
    total_expenses_usd = money(sum(line["amount_usd"] for line in expense_lines))
    return {
        "period": PERIOD,
        "revenue_usd": revenue_usd,
        "expense_lines": expense_lines,
        "total_expenses_usd": total_expenses_usd,
        "net_income_usd": money(revenue_usd - total_expenses_usd),
    }


def main() -> int:
    args = parse_args()
    json_dir = Path(args.json_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    recon_path = json_dir / "reconciliation_log.json"
    recon_rows = load_json(recon_path)

    receipts = []
    bank_rows = []
    card_rows = []
    receipts_path = json_dir / "receipts.json"
    bank_path = json_dir / "bank_transactions.json"
    card_path = json_dir / "credit_card_transactions.json"
    if receipts_path.is_file():
        receipts = load_json(receipts_path)
    if bank_path.is_file():
        bank_rows = load_json(bank_path)
    if card_path.is_file():
        card_rows = load_json(card_path)

    statement = build_statement(recon_rows, receipts, bank_rows, card_rows)
    output_path = out_dir / "income_statement_jan2026.json"
    output_path.write_text(json.dumps(statement, indent=2), encoding="utf-8")
    print(f"Wrote income statement to {output_path}")
    print(
        f"Revenue {statement['revenue_usd']:.2f} | "
        f"Expenses {statement['total_expenses_usd']:.2f} | "
        f"Net {statement['net_income_usd']:.2f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
