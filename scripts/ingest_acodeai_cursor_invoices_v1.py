#!/usr/bin/env python3
"""Ingest Cursor personal invoice zip/manifest into Token Spend Audit $ plane.

Expects extracted folder (default under data/acodeai/) with manifest.csv + PDFs.
Redacts email in public paste; keeps internal JSON research_only.

    py scripts/ingest_acodeai_cursor_invoices_v1.py
    py scripts/ingest_acodeai_cursor_invoices_v1.py --src data/acodeai/cursor_invoices_personal_all_v1
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SRC = ROOT / "data/acodeai/cursor_invoices_personal_all_v1"
OUT = ROOT / "docs/final/artifacts/acodeai_cursor_invoices_ingest_v1_latest.json"
PASTE = ROOT / "reports/human_paste/acodeai_cursor_invoices_ingest_elementary_2026-08-10.txt"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(p).replace("\\", "/")


def _fnum(s: str) -> float:
    try:
        return float(str(s).strip().replace(",", ""))
    except ValueError:
        return 0.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC)
    args = ap.parse_args()
    src: Path = args.src
    man = src / "manifest.csv"
    if not man.is_file():
        print(json.dumps({"ok": False, "err": f"missing {man}"}))
        return 2

    rows: list[dict[str, Any]] = []
    with man.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            amount = _fnum(r.get("Amount") or "0")
            rows.append(
                {
                    "date": (r.get("Date") or "").strip(),
                    "invoice_id": (r.get("Invoice ID") or "").strip(),
                    "description": (r.get("Description") or "").strip(),
                    "status": (r.get("Status") or "").strip(),
                    "amount_usd": amount,
                    "currency": (r.get("Currency") or "USD").strip(),
                    "file": (r.get("File") or "").strip(),
                    "pdf_exists": (src / (r.get("File") or "")).is_file(),
                }
            )

    rows_sorted = sorted(rows, key=lambda x: x["date"])
    paid = [x for x in rows_sorted if x["status"] == "paid"]
    total_paid = sum(x["amount_usd"] for x in paid)
    usage_rows = [x for x in rows_sorted if re.search(r"usage|cycle", x["description"], re.I)]
    usage_sum = sum(x["amount_usd"] for x in usage_rows)
    nonzero = [x for x in rows_sorted if x["amount_usd"] > 0]

    # PDF skim for plan labels (best-effort)
    plan_notes: list[str] = []
    try:
        import pypdf  # type: ignore

        for x in rows_sorted:
            fp = src / x["file"]
            if not fp.is_file():
                continue
            text = "\n".join(
                (pg.extract_text() or "") for pg in pypdf.PdfReader(str(fp)).pages
            )
            if re.search(r"Cursor Pro", text, re.I):
                plan_notes.append(f"{x['date']}: Cursor Pro mentioned")
            if re.search(r"Unused time", text, re.I):
                plan_notes.append(f"{x['date']}: unused-time credit/adjust")
    except Exception as e:
        plan_notes.append(f"pdf_skim_skip: {type(e).__name__}")

    art = {
        "schema": "acodeai_cursor_invoices_ingest_v1",
        "generated_at_utc": _utc(),
        "research_only": True,
        "send_gate": "HOLD",
        "pass_claimed": False,
        "product_all_ok": False,
        "cash_cow_proven": False,
        "provenance": "SELF_RUN_DEMO",
        "label_ko": "자체 실행 · 고객 사례 아님 · personal invoices",
        "source_dir": _rel(src),
        "n_invoices": len(rows_sorted),
        "rows": rows_sorted,
        "totals": {
            "paid_sum_usd": total_paid,
            "usage_cycle_sum_usd": usage_sum,
            "nonzero_count": len(nonzero),
            "currency": "USD",
        },
        "verdict_ko": (
            "최근 Usage cycle 청구는 $0.00 · Cursor 구독 $ 누수가 본선이 아님. "
            "과거 Pro/조정 유료 건은 있음. Token Spend Audit 본선은 외부 API/워크플로 측정."
        ),
        "plan_notes": plan_notes,
        "pii_wall_ko": "이메일·주소는 paste에 넣지 않음 · PDF는 로컬 data/ 비공개 취급",
        "walls_ko": [
            "invoice ingest ≠ cash_cow_proven",
            "usage $0 ≠ no token waste elsewhere",
            "research_only · SEND HOLD · harness≠product",
        ],
        "next_1": "refresh Audit onepager with $ plane · commander 판정",
        "reproduce": f"py scripts/ingest_acodeai_cursor_invoices_v1.py --src {_rel(src)}",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    PASTE.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(art, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "research_only · SEND HOLD · 자체 실행 · 고객 사례 아님",
        "",
        f"한줄: Cursor invoices {len(rows_sorted)}건 · paid합 ${total_paid:.2f} · "
        f"Usage cycle합 ${usage_sum:.2f} · 최근 usage=$0",
        "건별:",
    ]
    for x in rows_sorted:
        lines.append(
            f"  - {x['date']} · {x['status']} · ${x['amount_usd']:.2f} · "
            f"{(x['description'] or '(no desc)')[:60]}"
        )
    lines += [
        f"판정힌트: {art['verdict_ko']}",
        f"art: {_rel(OUT)}",
        f"재현: {art['reproduce']}",
        "",
    ]
    PASTE.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"ok": True, "n": len(rows_sorted), "paid_sum": total_paid, "usage_sum": usage_sum, "art": str(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
