# Security

## Do not publish

- Real Cursor invoice **PDFs** (often contain email / billing address)
- Raw Azure Cost / consumption dumps with subscription GUIDs if your policy forbids it
- `.env`, API keys, DPAPI blobs

## Safe publish

- Synthetic `fixtures/` only in this repo
- Aggregated `$` / KRW totals without PII
- Scripts that **prefer CSV/JSON totals** over PDF text dumps

## Report

Open a GitHub issue (private security contact TBD) — do not attach live invoices.
