#!/usr/bin/env python3
"""Build Azure ActualCost ResourceId breakdown table for a-codeai.

  py scripts/build_acodeai_external_api_resourceid_breakdown_v1.py

Reads data/acodeai/azure_cost_export_v1/cost_query_*_resource*.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/acodeai/azure_cost_export_v1"
OUT_JSON = ROOT / "docs/final/artifacts/acodeai_external_api_resourceid_breakdown_v1_latest.json"
OUT_MD = ROOT / "docs/final/artifacts/acodeai_external_api_resourceid_breakdown_v1_latest.md"
PASTE = ROOT / "reports/human_paste/acodeai_external_api_resourceid_breakdown_elementary_2026-08-10.txt"
ONEPAGER = ROOT / "docs/final/artifacts/acodeai_external_api_spend_audit_onepager_v1_latest.json"
ONEPAGER_MD = ROOT / "docs/final/artifacts/acodeai_external_api_spend_audit_onepager_v1_latest.md"

KRW_PER_USD = 1350.0


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(p).replace("\\", "/")


def _short_rid(rid: str) -> str:
    if not rid:
        return "?"
    parts = rid.rstrip("/").split("/")
    return parts[-1] if parts else rid[-60:]


def _load_query(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8-sig").strip()
    if not raw or raw.startswith("ERROR") or "Too Many Requests" in raw:
        return {"ok": False, "path": _rel(path), "err": (raw or "empty")[:160]}
    data = json.loads(raw)
    props = data.get("properties") or {}
    cols = [c.get("name") for c in (props.get("columns") or [])]
    rows = []
    for row in props.get("rows") or []:
        item = {cols[i]: row[i] for i in range(min(len(cols), len(row)))}
        rows.append(item)
    period = path.stem.replace("cost_query_", "")
    return {
        "ok": True,
        "path": _rel(path),
        "period": period,
        "columns": cols,
        "rows": rows,
        "cost_sum": round(sum(float(r.get("Cost") or 0) for r in rows), 6),
        "currency": (rows[0].get("Currency") if rows else None),
    }


def main() -> int:
    as_of = _utc()
    files = sorted(SRC.glob("cost_query_*resource*.json"))
    periods: list[dict[str, Any]] = []
    attribution: list[dict[str, Any]] = []
    known_dogfood_accounts = {"mkm-openai-eastus2"}
    orphan_candidates: list[dict[str, Any]] = []

    for fp in files:
        q = _load_query(fp)
        if not q.get("ok"):
            periods.append(q)
            continue
        periods.append(
            {
                "ok": True,
                "period": q["period"],
                "cost_sum": q["cost_sum"],
                "currency": q["currency"],
                "path": q["path"],
                "n_rows": len(q["rows"]),
            }
        )
        for r in q["rows"]:
            rid = str(r.get("ResourceId") or "")
            short = _short_rid(rid)
            cost = float(r.get("Cost") or 0)
            row = {
                "period": q["period"],
                "resource_short": short,
                "resource_id": rid,
                "meter_category": r.get("MeterCategory"),
                "meter_subcategory": r.get("MeterSubCategory"),
                "cost": round(cost, 6),
                "currency": r.get("Currency"),
                "usd_equiv_advisory": round(cost / KRW_PER_USD, 4)
                if r.get("Currency") == "KRW"
                else None,
                "known_dogfood_account": short in known_dogfood_accounts,
            }
            attribution.append(row)
            if short not in known_dogfood_accounts and cost > 0:
                orphan_candidates.append(row)

    # Aggregate by resource_short across periods
    by_res: dict[str, float] = {}
    by_meter: dict[str, float] = {}
    for a in attribution:
        by_res[a["resource_short"]] = by_res.get(a["resource_short"], 0.0) + a["cost"]
        key = f"{a.get('meter_category')}|{a.get('meter_subcategory')}"
        by_meter[key] = by_meter.get(key, 0.0) + a["cost"]

    dogfood_sum = sum(v for k, v in by_res.items() if k in known_dogfood_accounts)
    other_sum = sum(v for k, v in by_res.items() if k not in known_dogfood_accounts)
    total = dogfood_sum + other_sum

    if total > 0 and other_sum <= 0.01:
        attr_status = "ALL_KNOWN_DOGFOOD"
        attr_note = "관측 비용 전액이 알려진 dogfood 계정(mkm-openai-eastus2)에 귀속 · orphan 잔여≈0"
        suggest = "의도적 burn(안샌다) 확정 후보 — 최종은 지휘관 칸"
    elif other_sum > 0:
        attr_status = "HAS_NON_DOGFOOD_RESIDUAL"
        attr_note = f"알려진 dogfood 외 잔여 ₩{other_sum:,.2f} — 누수 후보 검토"
        suggest = "잔여 ResourceId를 확인 후 샌다/안샌다"
    else:
        attr_status = "EMPTY"
        attr_note = "분해 행 없음"
        suggest = "재조회"

    art = {
        "schema": "acodeai_external_api_resourceid_breakdown_v1",
        "generated_at_utc": as_of,
        "research_only": True,
        "send_gate": "HOLD",
        "pass_claimed": False,
        "product_all_ok": False,
        "cash_cow_proven": False,
        "status": "OK" if attribution else "EMPTY",
        "attribution_status": attr_status,
        "attribution_note_ko": attr_note,
        "suggest_verdict_candidate_ko": suggest,
        "final_commander_slot": "OPEN",
        "known_dogfood_accounts": sorted(known_dogfood_accounts),
        "totals": {
            "dogfood_krw": round(dogfood_sum, 4),
            "other_krw": round(other_sum, 4),
            "total_krw": round(total, 4),
            "currency": "KRW",
        },
        "by_resource_short_krw": {k: round(v, 4) for k, v in sorted(by_res.items(), key=lambda x: -x[1])},
        "by_meter_krw": {k: round(v, 4) for k, v in sorted(by_meter.items(), key=lambda x: -x[1])},
        "periods": periods,
        "rows": sorted(attribution, key=lambda x: (-x["cost"], x["period"])),
        "orphan_candidates": orphan_candidates,
        "alert_threshold_draft": {
            "threshold_krw": 30000,
            "status": "REVIEW_ONLY",
            "note_ko": "월 ₩30,000 초과 알림 — 미등록 초안",
        },
        "walls_ko": [
            "ResourceId≠deployment명 전부 · MeterSubCategory로 모델군 추정",
            "귀속 전액 dogfood ≠ cash_cow_proven",
            "≠ SEND · research_only",
        ],
        "reproduce": "py scripts/build_acodeai_external_api_resourceid_breakdown_v1.py",
        "next_1": "지휘관 최종 1줄: 의도적 burn(안샌다) / 샌다 / 보류",
    }
    OUT_JSON.write_text(json.dumps(art, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# a-codeai External API — ResourceId 분해",
        "",
        f"- **as_of:** `{as_of}`",
        "- **research_only · SEND HOLD · cash_cow_proven=false**",
        f"- **attribution_status:** `{attr_status}`",
        f"- **note:** {attr_note}",
        f"- **suggest:** {suggest}",
        f"- **totals:** dogfood ₩{dogfood_sum:,.2f} · other ₩{other_sum:,.2f} · total ₩{total:,.2f}",
        "",
        "## by ResourceId (short)",
    ]
    for k, v in sorted(by_res.items(), key=lambda x: -x[1]):
        tag = "DOGFOOD" if k in known_dogfood_accounts else "OTHER"
        lines.append(f"- `{k}` · ₩{v:,.4f} · {tag}")
    lines += ["", "## by Meter (Category|SubCategory)"]
    for k, v in sorted(by_meter.items(), key=lambda x: -x[1])[:20]:
        lines.append(f"- `{k}` · ₩{v:,.4f}")
    lines += ["", "## Period rows (top)"]
    for r in art["rows"][:25]:
        lines.append(
            f"- {r['period']} · `{r['resource_short']}` · {r.get('meter_subcategory')} · ₩{r['cost']:,.4f}"
        )
    lines += ["", "## NEXT-1", art["next_1"], "", f"artifact: `{_rel(OUT_JSON)}`", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    PASTE.parent.mkdir(parents=True, exist_ok=True)
    PASTE.write_text(
        "\n".join(
            [
                "research_only · SEND HOLD · product_all_ok=false · harness≠product · pass_claimed=false",
                "",
                f"한줄: ResourceId 분해 {attr_status} · dogfood₩{dogfood_sum:,.0f} other₩{other_sum:,.0f}",
                f"된것: {_rel(OUT_MD)}",
                "안된것: 지휘관 최종 칸 · cash_cow · SEND · ₩30k 알림 등록",
                f"다음1타: {art['next_1']}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    # Attach pointer to onepager
    if ONEPAGER.is_file():
        op = json.loads(ONEPAGER.read_text(encoding="utf-8-sig"))
        op["resourceid_breakdown"] = {
            "path": _rel(OUT_JSON),
            "attribution_status": attr_status,
            "totals": art["totals"],
            "suggest_verdict_candidate_ko": suggest,
        }
        ONEPAGER.write_text(json.dumps(op, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if ONEPAGER_MD.is_file():
        md = ONEPAGER_MD.read_text(encoding="utf-8")
        block = (
            "\n## ResourceId 분해\n\n"
            f"- status: `{attr_status}`\n"
            f"- dogfood ₩{dogfood_sum:,.2f} · other ₩{other_sum:,.2f}\n"
            f"- detail: `{_rel(OUT_MD)}`\n"
        )
        if "## ResourceId 분해" not in md:
            md = md.rstrip() + "\n" + block + "\n"
            ONEPAGER_MD.write_text(md, encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "attribution_status": attr_status,
                "dogfood_krw": round(dogfood_sum, 2),
                "other_krw": round(other_sum, 2),
                "json": _rel(OUT_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
