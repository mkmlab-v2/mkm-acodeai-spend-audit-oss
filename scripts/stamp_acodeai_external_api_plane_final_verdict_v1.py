#!/usr/bin/env python3
"""Stamp a-codeai external API final plane verdict (self-demo close).

Commander status paste NEXT-1 line:
  의도적 burn(안샌다) · 잔여 ₩30=미상·무해
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/final/artifacts/acodeai_external_api_plane_final_verdict_v1_latest.json"
PASTE = ROOT / "reports/human_paste/acodeai_external_api_plane_final_verdict_elementary_2026-08-10.txt"
ONEPAGER = ROOT / "docs/final/artifacts/acodeai_external_api_spend_audit_onepager_v1_latest.json"
ONEPAGER_MD = ROOT / "docs/final/artifacts/acodeai_external_api_spend_audit_onepager_v1_latest.md"
BREAKDOWN = ROOT / "docs/final/artifacts/acodeai_external_api_resourceid_breakdown_v1_latest.json"
CURSOR_V = ROOT / "docs/final/artifacts/acodeai_cursor_plane_verdict_v1_latest.json"
SPEECH_READY = ROOT / "reports/azure_speech_tts_readiness_v1_latest.json"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(p: Path) -> dict[str, Any]:
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}


def main() -> int:
    as_of = _utc()
    bd = _load(BREAKDOWN)
    speech = _load(SPEECH_READY)
    speech_note = None
    if speech:
        speech_note = {
            "artifact": "reports/azure_speech_tts_readiness_v1_latest.json",
            "present": True,
            "keys_head": list(speech.keys())[:12],
            "note_ko": "Speech readiness 아티팩트 존재 · 7월 live burn 단정은 아님 · 잔여=미상·무해 유지",
        }

    verdict_line = "의도적 burn(안샌다) · 잔여 ₩30=미상·무해"
    art = {
        "schema": "acodeai_external_api_plane_final_verdict_v1",
        "generated_at_utc": as_of,
        "research_only": True,
        "send_gate": "HOLD",
        "pass_claimed": False,
        "product_all_ok": False,
        "cash_cow_proven": False,
        "lane": "ms",
        "plane": "external_api_usd",
        "self_demo_lane": "CLOSED",
        "verdict_ko": verdict_line,
        "final_commander_slot": "CLOSED",
        "attribution": {
            "dogfood_pct": 99.83,
            "dogfood_krw": (bd.get("totals") or {}).get("dogfood_krw"),
            "other_krw": (bd.get("totals") or {}).get("other_krw"),
            "other_resource": "mkm-speech-prod",
            "other_disposition_ko": "미상·무해 · de minimis · 누수 수사 가치 없음",
        },
        "speech_memory_check": speech_note
        or {
            "present": False,
            "note_ko": "7월 Speech live 실험 디스크 확증 없음 · 잔여=미상·무해로 닫음",
        },
        "model_mix_fact_ko": (
            "GPT5 미터 ₩9,689 vs 표준 OpenAI ₩8,053 — 8월 청구 가파름의 주범=모델 믹스(측정)"
        ),
        "de_minimis_rule_draft": {
            "rule_ko": "잔여 < ₩1,000 → 자동 안샌다 편입 + 로그만",
            "status": "ADOPTED_DRAFT_V1",
            "threshold_krw": 1000,
        },
        "alert_threshold_draft": {
            "threshold_krw": 30000,
            "status": "REVIEW_ONLY",
            "note_ko": "월 ₩30,000 초과 알림 — 미등록",
        },
        "cursor_plane": {
            "verdict": (_load(CURSOR_V) or {}).get("verdict"),
            "scope": (_load(CURSOR_V) or {}).get("verdict_scope_ko"),
        },
        "season_close_ko": [
            "Cursor usage $0 · 안 샌다",
            "외부 API ₩17.7k · 의도적 burn(안샌다) · Speech ₩30 미상·무해",
            "자기 계정으로 cash cow 절감가치 증명 불가 · 샘플 마름",
            "다음 증거=외부 파일럿 감사 1장만 · 대외 접촉은 지휘관 명시 전 금지",
        ],
        "walls_ko": [
            "self-demo CLOSED ≠ cash_cow_proven",
            "모델 믹스 관찰 ≠ 고객 ROI 증명",
            "≠ SEND · research_only",
        ],
        "next_1": (
            "대기: 외부 파일럿 1곳 감사 1장 — 대외 접촉·SEND는 지휘관 명시 지시 전 착수 금지"
        ),
        "breakdown_path": "docs/final/artifacts/acodeai_external_api_resourceid_breakdown_v1_latest.md",
        "onepager_path": "docs/final/artifacts/acodeai_external_api_spend_audit_onepager_v1_latest.md",
    }
    OUT.write_text(json.dumps(art, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if ONEPAGER.is_file():
        op = _load(ONEPAGER)
        op["commander_final_verdict"] = {
            "verdict_ko": verdict_line,
            "final_commander_slot": "CLOSED",
            "self_demo_lane": "CLOSED",
            "as_of_utc": as_of,
            "stamp": "docs/final/artifacts/acodeai_external_api_plane_final_verdict_v1_latest.json",
        }
        op["verdict_ko"] = verdict_line
        op["next_1"] = art["next_1"]
        ONEPAGER.write_text(json.dumps(op, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if ONEPAGER_MD.is_file():
        md = ONEPAGER_MD.read_text(encoding="utf-8")
        block = (
            "\n## 지휘관 최종 판정 (외부 API $)\n\n"
            f"- **최종:** `{verdict_line}`\n"
            "- **self-demo lane:** CLOSED\n"
            f"- stamped `{as_of}`\n"
            f"- de minimis draft: 잔여 < ₩1,000 → 자동 안샌다+로그\n"
        )
        if "## 지휘관 최종 판정 (외부 API $)" not in md:
            md = md.rstrip() + "\n" + block + "\n"
            ONEPAGER_MD.write_text(md, encoding="utf-8")

    PASTE.write_text(
        "\n".join(
            [
                "research_only · SEND HOLD · product_all_ok=false · harness≠product · pass_claimed=false",
                "",
                f"한줄: {verdict_line} · self-demo CLOSED · cash_cow=false",
                "된것: final verdict stamp · de minimis <₩1k draft ADOPTED_DRAFT",
                "안된것: cash_cow · SEND · 외부 파일럿 · ₩30k 알림 등록",
                f"다음1타: {art['next_1']}",
                f"art: {OUT.as_posix()}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "verdict": verdict_line, "art": str(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
