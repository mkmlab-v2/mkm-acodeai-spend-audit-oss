#!/usr/bin/env python3
"""Stamp commander Cursor-plane verdict + advance next-1 to external API $ plane.

Source: commander paste MKM_STATUS (안 샌다 · Cursor 평면 한정 · NEXT-1 외부 API).
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/final/artifacts/acodeai_cursor_plane_verdict_v1_latest.json"
PASTE = ROOT / "reports/human_paste/acodeai_cursor_plane_verdict_elementary_2026-08-10.txt"
ONEPAGER = ROOT / "docs/final/artifacts/acodeai_cursor_self_spend_audit_onepager_v1_latest.json"
ONEPAGER_MD = ROOT / "docs/final/artifacts/acodeai_cursor_self_spend_audit_onepager_v1_latest.md"
CENTER_BUILD = ROOT / "scripts/build_acodeai_commander_center_v1.py"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    as_of = _utc()
    op = {}
    if ONEPAGER.is_file():
        op = json.loads(ONEPAGER.read_text(encoding="utf-8-sig"))

    art = {
        "schema": "acodeai_cursor_plane_verdict_v1",
        "generated_at_utc": as_of,
        "research_only": True,
        "send_gate": "HOLD",
        "pass_claimed": False,
        "product_all_ok": False,
        "cash_cow_proven": False,
        "lane": "ms",
        "plane": "cursor_usd",
        "verdict": "안 샌다",
        "verdict_scope_ko": "Cursor $ 평면 한정",
        "commander_status_paste_ack": True,
        "evidence_ko": [
            "Usage cycle 2026-04~06 연속 $0.00",
            "paid 합 $220.38 = 2025 구독/조정 고정비 (usage 누수 아님)",
            "usage $0 평면에서 Spend Audit이 줄일 Cursor $ 없음",
        ],
        "kept_walls_ko": [
            "stub saving_proxy ≠ commercial 47.5 SLA",
            "AZURE_CACHE_DELTA ≠ $",
            "음성(안 샌다) 보고 = 신뢰 데모 후보 · ≠ cash_cow_proven",
        ],
        "gaps_ko": [
            "외부 API $ 평면 미측정",
            "캐시 델타 30건 $ 환산 비어 있음",
        ],
        "onepager_path": "docs/final/artifacts/acodeai_cursor_self_spend_audit_onepager_v1_latest.md",
        "invoice_ingest_path": "docs/final/artifacts/acodeai_cursor_invoices_ingest_v1_latest.json",
        "next_1": "외부 API $ 평면 1장 — Azure/OpenAI 청구 export → data/acodeai/ → ingest+onepager",
        "blocked_until": "Azure OpenAI and/or OpenAI billing export dropped under data/acodeai/ or Downloads",
        "walls_ko": [
            "Cursor 안 샌다 ≠ 전체 안 샌다",
            "≠ SEND · ≠ cash_cow_proven · research_only",
        ],
    }
    OUT.write_text(json.dumps(art, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if op:
        op["commander_verdict_cursor_plane"] = {
            "verdict": "안 샌다",
            "scope_ko": "Cursor $ 평면 한정",
            "as_of_utc": as_of,
            "stamp": "docs/final/artifacts/acodeai_cursor_plane_verdict_v1_latest.json",
        }
        op["next_1"] = art["next_1"]
        ONEPAGER.write_text(json.dumps(op, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if ONEPAGER_MD.is_file():
        md = ONEPAGER_MD.read_text(encoding="utf-8")
        block = (
            "\n## 지휘관 판정 (Cursor $ 평면)\n\n"
            f"- **판정:** 안 샌다 (Cursor 평면 한정) · stamped `{as_of}`\n"
            "- **다음:** 외부 API $ 평면 1장 측정 (Azure/OpenAI export 필요)\n"
        )
        if "## 지휘관 판정 (Cursor $ 평면)" not in md:
            md = md.rstrip() + "\n" + block + "\n"
            ONEPAGER_MD.write_text(md, encoding="utf-8")

    PASTE.write_text(
        "\n".join(
            [
                "research_only · SEND HOLD · product_all_ok=false · harness≠product · pass_claimed=false",
                "",
                "한줄: Cursor $ 평면 판정=안 샌다 · 다음=외부 API $ 측정",
                "된것: verdict stamp + onepager 판정 칸 기입",
                "안된것: 외부 API export 없음 · cash_cow_proven · SEND",
                f"다음1타: {art['next_1']}",
                f"art: {OUT.as_posix()}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Advance center next-1 via builder constants (patched by caller before this, or we patch here)
    print(json.dumps({"ok": True, "verdict": "안 샌다", "art": str(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
