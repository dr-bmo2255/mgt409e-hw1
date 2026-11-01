#!/usr/bin/env python3
"""Extract structured rows from purchase receipt PDFs using an LLM."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from openai import OpenAI
from pypdf import PdfReader

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "receipts_extract.md"
REQUIRED_FIELDS = (
    "vendor",
    "date",
    "description",
    "amount_usd",
    "category",
    "source_file",
    "fields_not_found",
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
        description="Extract purchase receipt data from PDFs into JSON."
    )
    parser.add_argument(
        "--docs-dir",
        required=True,
        help="Path to the unzipped hw1_spoke_and_wrench document pack.",
    )
    parser.add_argument(
        "--out-dir",
        default="output",
        help="Directory where receipts.json will be written.",
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


def find_receipt_pdfs(docs_dir: Path) -> list[Path]:
    pdfs_dir = docs_dir / "pdfs"
    if not pdfs_dir.is_dir():
        raise FileNotFoundError(f"Expected PDF folder not found: {pdfs_dir}")

    receipts = sorted(pdfs_dir.glob("receipt_*.pdf"))
    ebay = pdfs_dir / "ebay_repair_stand.pdf"
    if ebay.is_file():
        receipts.append(ebay)
    return receipts


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


def normalize_row(row: dict, source_file: str) -> dict:
    normalized: dict = {"source_file": source_file}
    missing = row.get("fields_not_found")
    if not isinstance(missing, list):
        missing = []

    for field in REQUIRED_FIELDS:
        if field == "source_file":
            continue
        if field == "fields_not_found":
            normalized[field] = missing
            continue

        value = row.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            normalized[field] = None
            if field not in missing:
                missing.append(field)
        else:
            normalized[field] = value

    normalized["fields_not_found"] = sorted(set(missing))
    return normalized


def call_llm(client: OpenAI, prompt: str, pdf_text: str, source_file: str) -> dict:
    user_content = (
        f"Source file: {source_file}\n\n"
        f"Receipt text:\n{pdf_text}"
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
        raise ValueError(f"Empty LLM response for {source_file}")

    row = parse_json_response(raw)
    row["source_file"] = source_file
    return normalize_row(row, source_file)


def main() -> int:
    load_local_env()
    args = parse_args()
    docs_dir = Path(args.docs_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    prompt = load_prompt()
    client = make_client()
    receipt_pdfs = find_receipt_pdfs(docs_dir)

    if not receipt_pdfs:
        print("No purchase receipt PDFs found.", file=sys.stderr)
        return 1

    rows: list[dict] = []
    for pdf_path in receipt_pdfs:
        print(f"Processing {pdf_path.name}...")
        pdf_text = extract_pdf_text(pdf_path)
        row = call_llm(client, prompt, pdf_text, pdf_path.name)
        rows.append(row)

    output_path = out_dir / "receipts.json"
    output_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} rows to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
