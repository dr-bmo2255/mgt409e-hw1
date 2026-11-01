#!/usr/bin/env python3
"""Extract structured rows from the January bank statement using an LLM."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from openai import OpenAI
from pypdf import PdfReader

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "bank_extract.md"
BANK_PDF_NAME = "bank_statement_jan2026.pdf"
REQUIRED_FIELDS = (
    "date",
    "description",
    "amount_usd",
    "classification",
    "direction",
    "accounting_label",
    "expense_type",
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
        description="Extract bank statement lines into JSON."
    )
    parser.add_argument(
        "--docs-dir",
        required=True,
        help="Path to the unzipped hw1_spoke_and_wrench document pack.",
    )
    parser.add_argument(
        "--out-dir",
        default="output",
        help="Directory where bank_transactions.json will be written.",
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


def find_bank_pdf(docs_dir: Path) -> Path:
    pdf_path = docs_dir / "pdfs" / BANK_PDF_NAME
    if not pdf_path.is_file():
        raise FileNotFoundError(f"Bank statement not found: {pdf_path}")
    return pdf_path


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages).strip()
    if not text:
        raise ValueError(f"No extractable text found in {pdf_path.name}")
    return text


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
        if field == "expense_type":
            if value is None or (isinstance(value, str) and not value.strip()):
                normalized[field] = None
            else:
                normalized[field] = value
            continue

        if value is None or (isinstance(value, str) and not value.strip()):
            normalized[field] = None
        else:
            normalized[field] = value

    amount = normalized.get("amount_usd")
    if isinstance(amount, str):
        amount = float(amount.replace(",", "").replace("$", ""))
        normalized["amount_usd"] = amount
    if isinstance(amount, (int, float)) and amount < 0:
        normalized["amount_usd"] = abs(float(amount))

    label = normalized.get("accounting_label")
    if label != "expense":
        normalized["expense_type"] = None

    return normalized


def call_llm(client: OpenAI, prompt: str, pdf_text: str) -> list[dict]:
    user_content = (
        f"Source file: {BANK_PDF_NAME}\n\n"
        f"Bank statement text:\n{pdf_text}"
    )

    response = client.chat.completions.create(
        model=get_model(),
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    if not raw:
        raise ValueError("Empty LLM response for bank statement")

    payload = parse_json_response(raw)
    transactions = payload.get("transactions")
    if not isinstance(transactions, list):
        raise ValueError("LLM response missing a transactions array.")

    return [normalize_row(row) for row in transactions if isinstance(row, dict)]


def verify_against_statement(pdf_text: str, rows: list[dict]) -> None:
    """Light sanity check: count dated transaction lines on the statement."""
    line_pattern = re.compile(r"^(\d{2}/\d{2})\s", re.MULTILINE)
    statement_lines = line_pattern.findall(pdf_text)
    if len(rows) != len(statement_lines):
        print(
            f"Warning: extracted {len(rows)} rows but statement shows "
            f"{len(statement_lines)} dated transaction lines.",
            file=sys.stderr,
        )


def main() -> int:
    load_local_env()
    args = parse_args()
    docs_dir = Path(args.docs_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    prompt = load_prompt()
    client = make_client()
    bank_pdf = find_bank_pdf(docs_dir)

    print(f"Processing {bank_pdf.name}...")
    pdf_text = extract_pdf_text(bank_pdf)
    rows = call_llm(client, prompt, pdf_text)
    verify_against_statement(pdf_text, rows)

    output_path = out_dir / "bank_transactions.json"
    output_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} rows to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
