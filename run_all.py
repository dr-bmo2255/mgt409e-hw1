#!/usr/bin/env python3
"""Run the Homework 1 pipeline in order (Problems 2–5, 7–8)."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_local_env() -> None:
    env_path = ROOT / ".env"
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chain HW1 scripts. Does not overwrite judgment_calls.json or pipeline.html."
    )
    parser.add_argument(
        "--docs-dir",
        required=True,
        help="Path to the unzipped hw1_spoke_and_wrench document pack (not included in this zip).",
    )
    parser.add_argument("--json-dir", default="output")
    parser.add_argument("--out-dir", default="output")
    return parser.parse_args()


def run(cmd: list[str]) -> None:
    print(">", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=ROOT)


def main() -> int:
    load_local_env()
    args = parse_args()
    py = sys.executable
    docs = str(Path(args.docs_dir).resolve())
    json_dir = str(Path(args.json_dir).resolve())
    out_dir = str(Path(args.out_dir).resolve())
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    run([py, "read_receipts.py", "--docs-dir", docs, "--out-dir", out_dir])
    run([py, "read_bank.py", "--docs-dir", docs, "--out-dir", out_dir])
    run([py, "read_card.py", "--docs-dir", docs, "--out-dir", out_dir])
    run(
        [
            py,
            "reconcile.py",
            "--docs-dir",
            docs,
            "--json-dir",
            json_dir,
            "--out-dir",
            out_dir,
        ]
    )
    run([py, "income_statement.py", "--json-dir", json_dir, "--out-dir", out_dir])
    run(
        [
            py,
            "report.py",
            "--json-dir",
            json_dir,
            "--out",
            str(Path(out_dir) / "income_statement.html"),
        ]
    )
    print("Pipeline finished. judgment_calls.json and pipeline.html are left as submitted samples.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
