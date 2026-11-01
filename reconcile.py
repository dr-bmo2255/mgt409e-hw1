#!/usr/bin/env python3
"""Reconcile receipts, bank, and credit card data into an income-statement log."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from openai import OpenAI
from pypdf import PdfReader

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "reconcile.md"
REQUIRED_FIELDS = (
    "id",
    "sources",
    "amounts_seen",
    "included_in_income_statement",
    "amount_used_in_income_statement",
    "resolution",
)
RELEVANT_DOCS = (
    "emails/email_owner_voice_memo.txt",
    "emails/email_fleet_wellness.txt",
    "pdfs/receipt_park_tool.pdf",
    "pdfs/receipt_nhbp_parts.pdf",
    "pdfs/receipt_courier.pdf",
    "pdfs/receipt_home_depot.pdf",
    "pdfs/receipt_amazon_headphones.pdf",
    "pdfs/ebay_repair_stand.pdf",
    "pdfs/quote_hartford_mutual_fleet.pdf",
    "pdfs/iou_mike_smith.pdf",
    "pdfs/bank_statement_jan2026.pdf",
    "pdfs/credit_card_jan2026.pdf",
)


def load_local_env() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_model() -> str:
    return os.environ.get("OPENAI_MODEL", "gpt-5.6-luna")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reconcile extracted financial JSON into a decision log."
    )
    parser.add_argument(
        "--docs-dir",
        required=True,
        help="Path to the unzipped hw1_spoke_and_wrench document pack.",
    )
    parser.add_argument(
        "--json-dir",
        default="output",
        help="Directory containing receipts.json, bank_transactions.json, etc.",
    )
    parser.add_argument(
        "--out-dir",
        default="output",
        help="Directory where reconciliation_log.json will be written.",
    )
    return parser.parse_args()


def load_prompt() -> str:
    if not PROMPT_PATH.is_file():
        raise FileNotFoundError(f"Prompt file not found: {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding="utf-8")


def make_client() -> OpenAI:
    api_key = os.environ.get("PORTKEY_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Set PORTKEY_API_KEY or OPENAI_API_KEY before running this script."
        )

    if os.environ.get("PORTKEY_API_KEY"):
        return OpenAI(api_key=api_key, base_url="https://api.portkey.ai/v1")
    return OpenAI(api_key=api_key)


def load_json(path: Path) -> list | dict:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


def load_supporting_documents(docs_dir: Path) -> dict[str, str]:
    documents: dict[str, str] = {}
    for rel_path in RELEVANT_DOCS:
        path = docs_dir / rel_path
        if not path.is_file():
            continue
        if path.suffix.lower() == ".pdf":
            documents[path.name] = extract_pdf_text(path)
        else:
            documents[path.name] = path.read_text(encoding="utf-8")
    return documents


def parse_json_response(raw_text: str) -> dict:
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("LLM response was not a JSON object.")
    return data


def normalize_row(row: dict) -> dict:
    normalized: dict = {}

    for field in REQUIRED_FIELDS:
        value = row.get(field)
        if field == "sources":
            normalized[field] = list(value) if isinstance(value, list) else []
            continue
        if field == "amounts_seen":
            if not isinstance(value, dict):
                normalized[field] = {}
            else:
                normalized[field] = {
                    str(k): float(v) if v is not None else 0.0
                    for k, v in value.items()
                }
            continue
        if field == "included_in_income_statement":
            normalized[field] = str(value).strip().lower() if value is not None else "no"
            continue
        if field == "amount_used_in_income_statement":
            normalized[field] = float(value) if value is not None else 0.0
            continue
        normalized[field] = value

    if normalized["included_in_income_statement"] not in {"yes", "no"}:
        normalized["included_in_income_statement"] = "no"

    if normalized["included_in_income_statement"] == "no":
        normalized["amount_used_in_income_statement"] = 0.0

    return normalized


def build_user_payload(
    receipts: list,
    bank_rows: list,
    card_rows: list,
    documents: dict[str, str],
) -> str:
    sections = [
        "## receipts.json\n" + json.dumps(receipts, indent=2),
        "## bank_transactions.json\n" + json.dumps(bank_rows, indent=2),
        "## credit_card_transactions.json\n" + json.dumps(card_rows, indent=2),
    ]
    for name, text in documents.items():
        sections.append(f"## {name}\n{text}")
    return "\n\n".join(sections)


def call_llm(client: OpenAI, prompt: str, payload: str) -> list[dict]:
    response = client.chat.completions.create(
        model=get_model(),
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": payload},
        ],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    if not raw:
        raise ValueError("Empty LLM response for reconciliation")

    data = parse_json_response(raw)
    rows = data.get("reconciliation")
    if not isinstance(rows, list):
        raise ValueError("LLM response missing a reconciliation array.")

    return [normalize_row(row) for row in rows if isinstance(row, dict)]


def main() -> int:
    load_local_env()
    args = parse_args()
    docs_dir = Path(args.docs_dir).resolve()
    json_dir = Path(args.json_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    receipts_path = json_dir / "receipts.json"
    bank_path = json_dir / "bank_transactions.json"
    card_path = json_dir / "credit_card_transactions.json"

    for path in (receipts_path, bank_path, card_path):
        if not path.is_file():
            raise FileNotFoundError(f"Required JSON file not found: {path}")

    receipts = load_json(receipts_path)
    bank_rows = load_json(bank_path)
    card_rows = load_json(card_path)
    documents = load_supporting_documents(docs_dir)

    prompt = load_prompt()
    client = make_client()
    payload = build_user_payload(receipts, bank_rows, card_rows, documents)

    print("Reconciling extracted data with supporting documents...")
    rows = call_llm(client, prompt, payload)

    output_path = out_dir / "reconciliation_log.json"
    output_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} reconciled rows to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
