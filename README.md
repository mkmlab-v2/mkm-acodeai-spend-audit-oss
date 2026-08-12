# a-codeai Spend Audit — open core (research)

**Measure token/$ spend honestly. Do not invent a 47.5% savings headline.**

MIT · research_only · not a commercial SLA · not investment advice.

## Why this exists

We ran this audit on our own Cursor + Azure bills.

- Cursor usage cycles billed **$0** (subscription fixed cost ≠ usage leak).
- Azure ActualCost was real but **~99.8% dogfood-attributed** → intentional burn, not a leak story.
- Cache-delta advisory savings on that account were **de minimis in $**.

So the honest README claim is:

> This tool can report **「no leak / intentional burn」** when that is what the invoice says.
> It does **not** promise commercial 47.5% savings.

If your API bill is large, the same measurement plane is where savings (model mix, cache, routing) become meaningful.

## What ships (open)

| Piece | Role |
|-------|------|
| Cursor invoice CSV ingest | `$` plane from `manifest.csv` (no PDFs required) |
| External API ActualCost wrap | monthly provider sums + ResourceId breakdown helpers |
| One-pager builders | dual-plane report (Cursor vs external API) |
| Synthetic fixtures | reproducible smoke without personal invoices |

## What stays private (you provide)

| Asset | Why |
|-------|-----|
| Real invoice PDFs / Cost export JSON | PII (email, address) + tenant IDs |
| `.env` / Azure keys | secrets |
| Logos / Bible Ask | separate passion lane — not this SKU |

## Supported formats (v1)

- **Cursor:** `manifest.csv` columns `Date,Invoice ID,Description,Status,Amount,Currency,File` (File optional)
- **Azure:** Cost Management ActualCost query JSON (`cost_query_*.json`) and/or consumption usage JSON
- **OpenAI direct:** not wired in v1 (declare gap)

## 60-second smoke

```bash
py -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
py scripts/ingest_acodeai_cursor_invoices_v1.py --src fixtures/cursor_invoices_synthetic_v1
py scripts/run_acodeai_cursor_self_spend_audit_onepager_v1.py
```

Expect JSON under `docs/final/artifacts/` (created on first run) or adjust paths for your layout.

## Open vs paid (product wall)

| Open (door) | Closed (inside) |
|-------------|-----------------|
| Measure · attribute · honest one-pager | Routing · cache ops · monitoring as managed service |

## Success metric (operator)

Public release goal example: **inbound inquiry or external invoice contribution within 90 days**.  
Stars alone are not the metric.

## Related (opt-in research, not a product)

If the local synthetic try is useful and you may share **masked, non-secret** ops/ticket logs:  
[mkm-acodeai-icp-recruit-v1](https://github.com/mkmlab-v2/mkm-acodeai-icp-recruit-v1) · start at `TRY_BEFORE_CONTRIBUTE.md`.  
Issue ≠ ICP. No savings-% · no hosted API.

## Security

- Do **not** commit real PDFs or Cost exports with personal data.
- Redact emails/addresses before sharing artifacts.
- See `SECURITY.md`.

## License

MIT — see `LICENSE`.
