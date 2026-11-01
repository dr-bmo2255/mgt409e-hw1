# AI Prompts Log — Homework 1

This file records prompts typed to the vibe coder (Cursor AI) while working through Homework 1.  
It is **not** the same as the runtime `prompts/` folder used by scripts.

---

## Problem 1: Vibe coder prompts

**Screenshots shared:** Panel A (initial homework overview), Panel B (section requirements for Problems 2–9)

**Prompt:**
> SO. part A - create AI_prompts.md and keep it updated as we work. This is a file of what I type to you. There will br problems 2-9. For each section, I will let you know the question number. I want you to record what I typed to you in the AI_prompts.md file. Then if I require a second prompt to complete an assignment ask me to comment on what was missing and record that as well. Make note of each time I send you a screenshot of the problem Parts A & B.

**Second prompt needed?** No

---

## Problem 2: Read receipts

**Screenshots shared:** Panel A, Panel B

**Prompt:**
> Ok here is problem number 2. Create a scripts called read_receipts.py. THis will call on a LLM using the prompt in prompts/receipts_extract.md to extract 1 row per purchase receipt PDF in the folder. Save a JSON array of these rows to output/receipts.json. Each row will have the following columns - Vendor (store or seller name); date (of transaction); description (of item purchased; Amount_USD (total for the receipt in US $); category (using expense labes like "cogs_parts" "tools_equipments", "shipping" and other common accounting categories); Source_file (of which PDF you got this information. Any missing fields should go into "fields_not_found". I want the script to run wtih thet command format "python read_receipts.py --docs-dir PATH -- out-dir output". --docs-dir is the unzippered file pack.

**Second prompt needed?** No

**What was lacking after the first prompt:** *(n/a)*

---

## Problem 3: Read bank statement

**Screenshots shared:** Panel A, Panel B

**Prompt:**
> This is problem #3. We are now evaluating a bank statement. We will use the Jan bank statement and create structured data of it. Each line will need either a business or personal label and accounding category. Create a script called read_bank.py. This will call an LLM to use the prompt in prompts/bank_extract.md to extract each line from the bank_statement_jan2026.pdf. Save it in rows to a JSON array called output/bank_transactions.json. Each row will have the columns called: "Date" (of transaction/posting); "description" (the text on the statement); "amount_usd" (a positive number as a dollar amount); the "classification" (business vs personal); "direction" (whether it is a credit (money in) or a debit (money out); an "Accounting label" (common accounting terms - i.e revenue, expense, owner_draw, transfer) "expense type" with subcategories when it is a bank expense like (rent, utilities, cogs_parts...) and omit or null any otherwise. Verify that you did not invent or misread data. script needs to run with the command "python read_bank.py --docs-dir PATH -- out-dir output" then run that file and open the output for my review

**Second prompt needed?** No

**What was lacking after the first prompt:** *(n/a)*

---

## Problem 4: Read credit card statement

**Screenshots shared:** Panel A, Panel B

**Prompt:**
> Q 4- THis will separate business transactions from the owners credit card. Create new script called "read_card.py" Call on an LLM using promp in prompts/card_extract.md to sxtract each charge from credit_card_jan2026.pdf. Save a JSON array to output/credit_card_transactions.json. each credit charge must include: "date" of charge; "merchant" name on statement; "amount_usd" in $, "classification": business/personal; "expense_category" - use the same business expense labels that we used earlier for the shop charges. use "null" on the personal rows. Run the script with "python read_card.py --docs-dir PATH --out-dir output". Double check your work. don't invent values. open the files for my review

**Second prompt needed?** No

**What was lacking after the first prompt:** *(n/a)*

---

## Problem 5: Reconciliation log

**Screenshots shared:** Panel A, Panel B

**Prompt:**
> Open the REI pdf. and ask me again after you do #5 how I want REI categorized. Here is #5 - lets reconcile the charges. screate a script "reconcile.py" calling on an LLM using the prompt in prompts/reconcile.md to reconcile the amounts that appear in more than one document or need a single income-statement decision. Each row in the log is one reconciled amount, not just every line from problems 2-4. Pass in "outputs/receipts.json", "output/bank_transactions.json", "output/credit_card_transactions.json", plus any text from relevant documents. Save it as a JSON array to "output/reconciliation_log.json". Rows need to include: "ID" a short slug for the reconciled item. (eg park_tool_card_vs_receipt); "sources" (list of documents filenames used for this row); "amounts_seen" mapping each source filename to the dollar amount seen in that document - e.g "receipt_park_tool.pdf: 88.7"; "included_in_income_statement" Yes/no; should this row count toward January revenue or expenses?; "Amount_used_in_income_statement": dollar amount to book after reconciliation (Use 0 if excluded); "resolution" using plain english explaining how you matched these documents and chose the final amount. Run this with "python reconcile.py -- docs-dir Path --json-dir output --out-dir output. double check your work. don't invent values. open the documents for my review. don't forget to revisit the question on REI.

**Second prompt needed?** No

**What was lacking after the first prompt:** *(n/a)*

**Follow-up clarification (REI):**
> ok. REI is a business expense. and it is equipment.

Updated `output/credit_card_transactions.json` (REI → `business`, `tools_equipment`) and `output/reconciliation_log.json` (book $156 as January business expense).

---

## Problem 6: Judgment calls

**Screenshots shared:** Panel A, Panel B

**Prompt:**
> so Q6 - create a file called "output/judgement_calls.json" as a JSON arroy of 3 objects - find me 3 rows in the reconciliation log where there is uncertainty in the amounts reconciled - where it was hardest to set "included_in_income_statement" or "amount_used_in_income_statement". present each of these to me individually with all supporting evidence to make a decision. then record the "transaction_id" from the reconciliation ID, "included_in_income_statement" "amount_used_in_income_statement", "evidence_for" (a bulleted list of document names),and a confidence (as high/medium/low) at least one of these you present me must be a low confidence. Then you will record my final decision for each line.

**Second prompt needed?** Yes — the first prompt asked to present each judgment call individually and wait for a decision; it did not include the three final include/amount choices.

**What was lacking after the first prompt:** Needed your include/amount decision on each of the three uncertain reconciliation rows.

**Your final decisions:**
1. `mixed_square_deposit_personal_portion` — included; amount $465 (business portion of the $560 deposit).
2. `hartford_mutual_march_quote` — not included for January; $0. Contract only; no service yet; revisit next month.
3. `park_tool_receipt_vs_card` — included at $127.40 (spanner shipped 1/12, presumed received by month-end). $344.55 stays a separate row.

---

## Problem 7: January income statement

**Screenshots shared:** Panel A, Panel B

**Prompt:**
> lets build an income satement. create script "income_statement.py" reading the output/reconciliation_log.json and take every row with "included_in_income_statement" = yes into revenue and expense lines. Save the January income statement to output/income_statement_jan2026.json. The math can come from basic python (without LLM) but our inputs must come from the reconcile step, NOT HARDCODED VALUES. Json array must include "period" (2026-01), revenue_usd, expense_lines (each with label, amount_usd, category, sources), "total_expenses_usd", and "net_income_usd. Run the script with "python income_statement.py --json-dir output --out-dir output. double check the numbers. don't invent values. open the file for my review.

**Second prompt needed?** No

**What was lacking after the first prompt:** *(n/a)*

---

## Problem 8: Income statement webpage

**Screenshots shared:** Panel A, Panel B

**Prompt:**
> create report.py reading the json files in output/ and make a one-page HTML summary. save it to output/income_statement.html. use the same numbers as the JSON. do not hand-edit or re-edit the totals in HTML. be sure to include - January income statement with all revenue, expenses, net income), the personal and business rows that were excluded. The 3 judgement calls. give the entire HTML page an old bank vibe with brass, green bank lamp glass, oak, and leather. run the script with python report.py --json-dir output --out output/income_statement.html. then open that page for me in edge browser for my review. Again - double check it, do not invent data. In fact for the rest of the project, be sure to double check, don't invent data, and always open your product for my review.

**Second prompt needed?** No

**What was lacking after the first prompt:** *(n/a)*

---

## Problem 9: Process flow diagram

**Screenshots shared:** Panel A, Panel B

**Prompt:**
> ok HTML looks good. Q9 - lets create a workflow diagram. make a one-page HTML file called output/pipeline.html with a block diagram of this income statement workflow. review q2-8. make one block per script created. add blocks for key inputs like (document pack, pdf, emails) and outputs (each JSON or HTML file) show arrows from these inputs, through the scripts to the outputs. In someway mark / identify where a LLM is called in each instanace. Do not create a python script for this and because my HTML coding skills stopped developing in 2000, i'm asking you to do all the HTML coding. Keep the same bank theming we had in the last one. Create a small logo this time for Spoke & Wrench Bicyle repair - put it in the upper left of the webpage. Be sure to make very VISUALLY clear each script name and what it reads and writes. Which steps are calling on the LLM and the pathway from the document pack to the income statement. I have a good idea. Everytime a LLM is used, on the top right corner of the flowchart block, put a robot emoji and the phrase "LLM used for this step" ok go.

**Second prompt needed?** Yes

**What was lacking after the first prompt:** The LLM badge sat on top of the script name/text in the flowchart blocks and needed a layout fix so the robot label and the Reads/Writes text do not overlap.

**Follow-up prompt:**
> In the HTML page from Q9, the little box with the robot emoji is covering up some text in the flowchart box. can you fix that so there is no overlap.

---

## Problem 10: Submission format

**Screenshots shared:** Panel A, Panel B

**Prompt:**
> Then...Pause here....this is the last step - Q10. these problems sets are going to be graded by the TAs and prof by using AI as well. so, lets package this entire problem set up so that the reviewer can install the dependencies, rerun the workflow pipeline, review all of my prompts and the outputs. This whole problem set needs to be entirely reproduceable. Put everything into a folder called hw1 and zip it into hw1.zip and open the folder that houses it for me to upload to Canvas. I need all scripts from Q2-8. I need the prompts/ with the runtime prompt files (prompts/*.md) that the scripts read) Include requirements.txt (openai and the PDF library). Include a readme.md with install steps, how to set the environment variables (like OpenAI_ApI_Key) ina local .env file. including the model name, and how to run each script. DO NOT INCLUDE MY ACTUAL API KEY in either the readme or the zip file. include all AI_Prompts.md that we set forth in Q1. Give a sample output/ from one successful run, including pipeline.html. then create run_all.py to chain the scrips in order. Review the file structure diagram denoted in the screenshot. Again don't place my APIKey in the files for upload.

**Second prompt needed?** No

**What was lacking after the first prompt:** *(n/a)*
