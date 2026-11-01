# MGT 409E HW1: Spoke & Wrench Income Statement

A class project for Yale SOM MGT 409E, AI Foundations for Managers. AI reads a bike shop's January 2026 receipts, bank statement and card statement, reconciles them, and feeds an income statement built with plain Python.

## Live pages

- [Demo](https://dr-bmo2255.github.io/mgt409e-hw1/)
- [Workflow map](https://dr-bmo2255.github.io/mgt409e-hw1/output/pipeline.html)
- [Submitted income statement](https://dr-bmo2255.github.io/mgt409e-hw1/output/income_statement.html)

## January 2026 result

| | Amount |
|---|---:|
| Revenue | $8,150.00 |
| Expenses | $4,618.32 |
| Net income | $3,531.68 |

## What's here

- `read_receipts.py`, `read_bank.py`, `read_card.py`, `reconcile.py`: steps that call an LLM
- `income_statement.py`, `report.py`: Python-only steps
- `run_all.py`: runs the pipeline in order
- `prompts/`: the prompts those scripts send to the LLM
- `output/`: saved results from one successful run
- `AI_prompts.md`: the prompts typed while building the project
- `build_demo.py`: rebuilds `index.html` from `output/`, without an LLM

## Rerunning it

The source PDFs and emails are private and aren't in this repo. The saved results can be viewed as they are, and `python build_demo.py` works without them. Rerunning the full pipeline needs your own copy of the document pack:

```bash
python -m pip install -r requirements.txt
cp .env.example .env
python run_all.py --docs-dir PATH_TO_DOCUMENT_PACK --json-dir output --out-dir output
```

Put your key in `.env`, which git ignores. The pipeline uses Portkey when `PORTKEY_API_KEY` is set and `OPENAI_API_KEY` otherwise. The default model is `gpt-5.6-luna`, and `OPENAI_MODEL` overrides it.
