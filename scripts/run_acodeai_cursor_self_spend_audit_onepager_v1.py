#!/usr/bin/env python3
"""Cursor/자체 spend Token Spend Audit 1장 (SELF_RUN_DEMO · now).

Commander ACK: 「ACK center change · dogfood: Cursor/자체 spend Audit 1장 … 지금 바로 해」

Assembles local dogfood metering + commander self_traffic + Azure dogfood wrap.
Does NOT invent Cursor.com invoice dollars when CSV is absent.

    py scripts/run_acodeai_cursor_self_spend_audit_onepager_v1.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "docs/final/artifacts/acodeai_cursor_self_spend_audit_onepager_v1_latest.json"
OUT_MD = ROOT / "docs/final/artifacts/acodeai_cursor_self_spend_audit_onepager_v1_latest.md"
PASTE = ROOT / "reports/human_paste/acodeai_cursor_self_spend_audit_onepager_elementary_2026-08-10.txt"

METER_SUMMARY = ROOT / "docs/final/artifacts/track_a_metering_summary_mkm-internal-dogfood-v4-cursor_latest.json"
METER_LOG = ROOT / "reports/constitution/btrack_pilot/track_a_metering_log_mkm-internal-dogfood-v4-cursor_v1.jsonl"
ONEPAGER = ROOT / "docs/final/artifacts/compression_dogfood_v4_cursor_internal_evidence_onepager_v1_latest.json"
SELF_TRAFFIC = ROOT / "docs/final/artifacts/acodeai_commander_self_traffic_intake_v1_latest.json"
AZURE_DOGFOOD = ROOT / "docs/final/artifacts/acodeai_azure_dogfood_paid_pilot_v1_latest.json"
A2A_USAGE = ROOT / "reports/a2a_tier3_cursor_usage_count_v1_latest.json"
CENTER = ROOT / "docs/final/artifacts/acodeai_commander_center_v1_latest.json"
INVOICES = ROOT / "docs/final/artifacts/acodeai_cursor_invoices_ingest_v1_latest.json"

ACK = (
    "ACK center change · dogfood: Cursor/자체 spend Audit 1장 내일이 아니라 지금 바로 해"
)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(p: Path) -> dict[str, Any]:
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}


def _rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(p).replace("\\", "/")


def _meter_log_stats(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"events": 0}
    before = after = 0
    n = 0
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        n += 1
        before += int(row.get("tokens_before") or row.get("token_before") or 0)
        after += int(row.get("tokens_after") or row.get("token_after") or 0)
    saving = ((before - after) / before) if before else None
    return {
        "events": n,
        "tokens_before": before,
        "tokens_after": after,
        "global_saving_rate_proxy": saving,
        "label_ko": "operational/stub metering · ≠ Cursor invoice · ≠ customer ROI",
    }


def _refresh_internal_onepager() -> dict[str, Any]:
    script = ROOT / "scripts/build_compression_dogfood_v4_cursor_internal_evidence_onepager_v1.py"
    if not script.is_file():
        return {"ok": False, "err": "missing onepager builder"}
    proc = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    return {
        "ok": proc.returncode == 0,
        "exit": proc.returncode,
        "stderr_tail": (proc.stderr or proc.stdout or "")[-400:],
    }


def main() -> int:
    as_of = _utc()
    # Refresh compression dogfood evidence one-pager (best-effort).
    refresh = _refresh_internal_onepager()

    summary = _load(METER_SUMMARY)
    onepager = _load(ONEPAGER)
    self_tr = _load(SELF_TRAFFIC)
    azure = _load(AZURE_DOGFOOD)
    a2a = _load(A2A_USAGE)
    invoices = _load(INVOICES)
    meter = _meter_log_stats(METER_LOG)

    # Prefer live JSONL counts; fall back to summary aggregates.
    if meter["events"] == 0 and summary:
        meter = {
            "events": int(summary.get("events_total") or 0),
            "tokens_before": int(summary.get("tokens_before_total") or summary.get("tokens_before") or 0),
            "tokens_after": int(summary.get("tokens_after_total") or summary.get("tokens_after") or 0),
            "global_saving_rate_proxy": summary.get("global_saving_rate"),
            "label_ko": "from metering summary fallback · ≠ Cursor invoice",
        }

    gaps = [
        "This page ≠ cash_cow_proven · ≠ B3 customer · ≠ SEND OPEN",
        "Metering saving_rate is stub/operational observation — not sales % SLA",
    ]
    if not invoices:
        gaps.insert(
            0,
            "Cursor invoices not ingested yet — run ingest_acodeai_cursor_invoices_v1.py",
        )
    else:
        gaps.insert(
            0,
            "Cursor usage cycle $0 ≠ external Azure/OpenAI spend measured — those remain separate plane",
        )

    measured_ok = meter.get("events", 0) > 0 or bool(self_tr) or bool(azure) or bool(invoices)

    inv_totals = (invoices.get("totals") or {}) if invoices else {}
    art = {
        "schema": "acodeai_cursor_self_spend_audit_onepager_v1",
        "generated_at_utc": as_of,
        "research_only": True,
        "send_gate": "HOLD",
        "pass_claimed": False,
        "product_all_ok": False,
        "cash_cow_proven": False,
        "provenance": "SELF_RUN_DEMO",
        "label_ko": "자체 실행 · 고객 사례 아님",
        "commander_ack": ACK,
        "locked_next_1": "dogfood: Cursor/자체 spend Audit 1장",
        "sku_frame": "token_spend_audit",
        "status": "ONEPAGER_STAMPED" if measured_ok else "GAP_NO_METER",
        "onepager_refresh": refresh,
        "planes": {
            "cursor_invoices_usd": {
                "ingested": bool(invoices),
                "n_invoices": invoices.get("n_invoices") if invoices else 0,
                "paid_sum_usd": inv_totals.get("paid_sum_usd"),
                "usage_cycle_sum_usd": inv_totals.get("usage_cycle_sum_usd"),
                "verdict_ko": invoices.get("verdict_ko") if invoices else None,
                "path": _rel(INVOICES) if INVOICES.is_file() else None,
            },
            "metering_dogfood_v4_cursor": {
                "tenant": "mkm-internal-dogfood-v4-cursor",
                "events": meter.get("events"),
                "tokens_before": meter.get("tokens_before"),
                "tokens_after": meter.get("tokens_after"),
                "global_saving_rate_proxy": meter.get("global_saving_rate_proxy"),
                "label_ko": meter.get("label_ko"),
                "paths": {
                    "meter_log": _rel(METER_LOG),
                    "summary": _rel(METER_SUMMARY) if METER_SUMMARY.is_file() else None,
                    "internal_onepager": _rel(ONEPAGER) if ONEPAGER.is_file() else None,
                },
            },
            "commander_self_traffic": {
                "status": self_tr.get("status"),
                "scrubbed_cases": self_tr.get("scrubbed_cases"),
                "path": _rel(SELF_TRAFFIC) if SELF_TRAFFIC.is_file() else None,
            },
            "azure_dogfood_wrap": {
                "status": azure.get("status") or azure.get("decision"),
                "path": _rel(AZURE_DOGFOOD) if AZURE_DOGFOOD.is_file() else None,
                "note_ko": "paid wrap / offline measured — see artifact; ≠ Cursor invoice",
            },
            "cursor_activity_proxy_a2a": {
                "path": _rel(A2A_USAGE) if A2A_USAGE.is_file() else None,
                "total_refs": a2a.get("total_refs"),
                "as_of": a2a.get("as_of_kst") or a2a.get("generated_at"),
                "label_ko": "activity proxy only · ≠ token $ · ≠ quality",
            },
        },
        "gaps_ko": gaps,
        "walls_ko": [
            "SELF_RUN_DEMO ≠ customer case",
            "waitlist surface may stay LIVE · mass cold/resend still forbidden",
            "harness≠product · research_only · SEND HOLD",
            "FAIL-COMP-004 · no Logos merge into a-codeai headline",
            "do not headline metering 0.47 as commercial 47.5% SLA",
        ],
        "commander_read_prompt_ko": (
            "Cursor 청구서(Usage $0) + dogfood 미터링을 보고 "
            "「샌다 / 안 샌다 / 쓸모없다」중 하나로 답해 주세요. "
            "Cursor 구독 $ 본선이 아니면 외부 API 평면으로 넘깁니다."
        ),
        "next_1": (
            "지휘관 판정(샌다/안샌다/쓸모없다) · "
            "Usage $0이면 next=외부 Azure/OpenAI spend 평면"
        ),
        "reproduce": (
            "py scripts/ingest_acodeai_cursor_invoices_v1.py && "
            "py scripts/run_acodeai_cursor_self_spend_audit_onepager_v1.py"
        ),
        "center_path": _rel(CENTER),
    }

    # Elementary MD one-pager
    tb = meter.get("tokens_before")
    ta = meter.get("tokens_after")
    sr = meter.get("global_saving_rate_proxy")
    sr_s = f"{sr:.4f}" if isinstance(sr, (int, float)) else "n/a"
    paid_sum = inv_totals.get("paid_sum_usd")
    usage_sum = inv_totals.get("usage_cycle_sum_usd")
    md = "\n".join(
        [
            "# a-codeai · Cursor/자체 spend Audit 1장 (SELF_RUN_DEMO)",
            "",
            f"- generated: `{as_of}`",
            f"- ACK: `{ACK}`",
            "- label: **자체 실행 · 고객 사례 아님**",
            "- send_gate: **HOLD** · cash_cow_proven: **false**",
            "",
            "## 한줄",
            "",
            (
                f"Cursor invoices ingested · paid합 "
                f"${paid_sum if paid_sum is not None else 'n/a'} · "
                f"Usage cycle합 ${usage_sum if usage_sum is not None else 'n/a'} · "
                "최근 Usage=$0 → Cursor $ 누수 본선 아님. "
                "로컬 dogfood 미터링은 별도 stub 평면."
                if invoices
                else "로컬 Cursor dogfood 미터링 + (청구서 미섭취)."
            ),
            "",
            "## A. Cursor invoices ($ plane)",
            "",
        ]
        + (
            [
                f"| 항목 | 값 |",
                f"|---|---|",
                f"| n_invoices | `{invoices.get('n_invoices')}` |",
                f"| paid_sum_usd | `${paid_sum}` |",
                f"| usage_cycle_sum_usd | `${usage_sum}` |",
                f"| verdict | {invoices.get('verdict_ko')} |",
                "",
                "### rows",
                "",
            ]
            + [
                f"- `{r.get('date')}` · {r.get('status')} · "
                f"${float(r.get('amount_usd') or 0):.2f} · "
                f"{(r.get('description') or '(no desc)')[:70]}"
                for r in (invoices.get("rows") or [])
            ]
            + [""]
            if invoices
            else ["- (not ingested)", ""]
        )
        + [
            "## B. Metering plane (dogfood stub · ≠ sales SLA)",
            "",
            f"| 항목 | 값 |",
            f"|---|---|",
            f"| tenant | `mkm-internal-dogfood-v4-cursor` |",
            f"| events | `{meter.get('events')}` |",
            f"| tokens_before → after | `{tb}` → `{ta}` |",
            f"| saving_rate_proxy | `{sr_s}` (**≠ 47.5 commercial**) |",
            f"| label | operational/stub |",
            "",
            "## C. 보조 증거",
            "",
            f"- commander_self_traffic: `{self_tr.get('status')}` · cases=`{self_tr.get('scrubbed_cases')}`",
            f"- azure_dogfood wrap: present=`{bool(azure)}`",
            f"- A2A cursor activity proxy total_refs=`{a2a.get('total_refs')}` (≠$)",
            "",
            "## GAP",
            "",
            *[f"- {g}" for g in gaps],
            "",
            "## 지휘관 판정 칸",
            "",
            art["commander_read_prompt_ko"],
            "",
            "## Reproduce",
            "",
            "```text",
            art["reproduce"],
            "```",
            "",
        ]
    )
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    PASTE.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(art, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(md, encoding="utf-8")
    PASTE.write_text(
        "\n".join(
            [
                "research_only · SEND HOLD · product_all_ok=false · harness≠product · pass_claimed=false",
                "자체 실행 · 고객 사례 아님",
                "",
                f"한줄: Cursor invoices + dogfood Audit · paid=${paid_sum} · "
                f"usage=${usage_sum} · meter {tb}→{ta} · Cursor$본선=아님",
                f"된것: ingest+onepager · art {_rel(OUT_JSON)}",
                "안된것: cash_cow_proven · 외부 API $ 평면 완결 · SEND",
                f"다음1타: {art['next_1']}",
                f"재현: {art['reproduce']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": measured_ok,
                "events": meter.get("events"),
                "tokens_before": tb,
                "tokens_after": ta,
                "saving_proxy": sr,
                "invoice_paid_sum": paid_sum,
                "invoice_usage_sum": usage_sum,
                "art": str(OUT_JSON),
                "md": str(OUT_MD),
            },
            ensure_ascii=False,
        )
    )
    return 0 if measured_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
