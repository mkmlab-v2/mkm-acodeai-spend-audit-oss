#!/usr/bin/env python3
"""External API $ plane Token Spend Audit 1장 (a-codeai).

Cursor plane already stamped 「안 샌다」. This stamps Azure/OpenAI plane:
  - Azure Cost Management ActualCost (az rest) under data/acodeai/azure_cost_export_v1/
  - Cache-Delta 30 measured JSONL → advisory USD (≠ invoice)

  py scripts/run_acodeai_external_api_spend_audit_onepager_v1.py

research_only · SEND HOLD · ≠ cash_cow_proven · advisory ≠ invoice
"""
from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "docs/final/artifacts/acodeai_external_api_spend_audit_onepager_v1_latest.json"
OUT_MD = ROOT / "docs/final/artifacts/acodeai_external_api_spend_audit_onepager_v1_latest.md"
PASTE = ROOT / "reports/human_paste/acodeai_external_api_spend_audit_onepager_elementary_2026-08-10.txt"
DATA_DIR = ROOT / "data/acodeai"
SELF_TRAFFIC_JSONL = (
    ROOT / "data/compression/acodeai_cache_delta_scrubbed_measured_commander_self_traffic_v1.jsonl"
)
SELF_TRAFFIC_GATE = (
    ROOT / "docs/final/artifacts/acodeai_cache_delta_gate_commander_self_traffic_azure_mkm_live_v1_latest.json"
)
SELF_TRAFFIC_RUN = (
    ROOT / "docs/final/artifacts/acodeai_cache_delta_commander_self_traffic_azure_mkm_live_run_v1_latest.json"
)
CURSOR_VERDICT = ROOT / "docs/final/artifacts/acodeai_cursor_plane_verdict_v1_latest.json"
CENTER = ROOT / "docs/final/artifacts/acodeai_commander_center_v1_latest.json"

ADVISORY_PRICE = {
    "model_class": "gpt-4o-mini",
    "input_usd_per_1m": 0.15,
    "cached_input_usd_per_1m": 0.075,
    "output_usd_per_1m": 0.60,
    "source_ko": "공개 단가표 가정(advisory) · Azure Cost Management/청구서 아님 · 단가 drift 가능",
}

# FX for display only — ActualCost currency stays KRW when returned as KRW.
KRW_PER_USD_ADVISORY = 1350.0


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(p).replace("\\", "/")


def _load(p: Path) -> dict[str, Any]:
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}


def _fnum(s: Any) -> float:
    try:
        return float(str(s).strip().replace(",", "").replace("$", ""))
    except (TypeError, ValueError):
        return 0.0


def _usage_cost(usage: dict[str, Any] | None) -> dict[str, float]:
    u = usage or {}
    prompt = int(u.get("prompt_tokens") or 0)
    completion = int(u.get("completion_tokens") or 0)
    details = u.get("prompt_tokens_details") or {}
    cached = int(u.get("cached_tokens") or details.get("cached_tokens") or 0)
    cached = min(cached, prompt)
    uncached = max(prompt - cached, 0)
    pin = ADVISORY_PRICE["input_usd_per_1m"]
    pcache = ADVISORY_PRICE["cached_input_usd_per_1m"]
    pout = ADVISORY_PRICE["output_usd_per_1m"]
    cost = (
        uncached / 1_000_000.0 * pin
        + cached / 1_000_000.0 * pcache
        + completion / 1_000_000.0 * pout
    )
    cost_no_cache = prompt / 1_000_000.0 * pin + completion / 1_000_000.0 * pout
    return {
        "prompt_tokens": float(prompt),
        "completion_tokens": float(completion),
        "cached_tokens": float(cached),
        "cost_usd_advisory": round(cost, 8),
        "cost_usd_advisory_no_cache": round(cost_no_cache, 8),
        "cache_saving_usd_advisory": round(cost_no_cache - cost, 8),
    }


def _ingest_cost_query_json(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8-sig").strip()
    if not raw or raw.startswith("ERROR") or "Too Many Requests" in raw:
        return {"path": _rel(path), "ok": False, "err": (raw or "empty")[:200]}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return {"path": _rel(path), "ok": False, "err": str(e)}
    if isinstance(data, dict) and data.get("error"):
        return {"path": _rel(path), "ok": False, "err": str(data.get("error"))[:200]}
    props = data.get("properties") or {}
    cols = [c.get("name") for c in (props.get("columns") or [])]
    rows_raw = props.get("rows") or []
    parsed: list[dict[str, Any]] = []
    total = 0.0
    currency = None
    for row in rows_raw:
        item = {cols[i]: row[i] for i in range(min(len(cols), len(row)))}
        cost = _fnum(item.get("Cost"))
        total += cost
        currency = item.get("Currency") or currency
        parsed.append(item)
    period = path.stem.replace("cost_query_", "")
    return {
        "path": _rel(path),
        "ok": True,
        "period": period,
        "columns": cols,
        "rows": parsed,
        "cost_sum": round(total, 6),
        "currency": currency,
        "cost_readable": bool(parsed),
    }


def _ingest_consumption_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as e:
        return {"path": _rel(path), "ok": False, "err": str(e)}
    if not isinstance(data, list):
        return {"path": _rel(path), "ok": False, "err": "not_list"}
    products: dict[str, int] = {}
    accounts: set[str] = set()
    pretax_sum = 0.0
    pretax_numeric = 0
    for row in data:
        prod = str(row.get("product") or "?")
        products[prod] = products.get(prod, 0) + 1
        inst = str(row.get("instanceName") or "")
        if "CognitiveServices" in inst or "openai" in inst.lower():
            accounts.add(inst.rstrip("/").split("/")[-1] or inst[-80:])
        pc = row.get("pretaxCost")
        if pc not in (None, "None", "", "null"):
            pretax_sum += _fnum(pc)
            pretax_numeric += 1
    return {
        "path": _rel(path),
        "ok": True,
        "n_rows": len(data),
        "products": dict(sorted(products.items(), key=lambda kv: -kv[1])),
        "openai_accounts": sorted(accounts),
        "pretax_cost_sum": round(pretax_sum, 6) if pretax_numeric else None,
        "pretax_numeric_rows": pretax_numeric,
        "cost_readable": pretax_numeric > 0 and pretax_sum > 0,
    }


def _scan_billing_exports(data_dir: Path) -> dict[str, Any]:
    hits: list[dict[str, Any]] = []
    consumption: list[dict[str, Any]] = []
    cost_queries: list[dict[str, Any]] = []
    if not data_dir.is_dir():
        return {
            "found": False,
            "files": [],
            "paid_sum_usd": None,
            "rows": 0,
            "consumption_exports": [],
            "cost_management_queries": [],
        }

    files: list[Path] = []
    for pat in ("*azure*", "*openai*", "*billing*", "*cost*", "*usage*", "*invoice*"):
        files.extend(data_dir.rglob(pat))
    seen: set[str] = set()
    uniq: list[Path] = []
    for f in files:
        if not f.is_file():
            continue
        key = str(f.resolve()).lower()
        if key in seen:
            continue
        if f.name.startswith("_") or f.name.startswith("README"):
            continue
        if f.suffix.lower() not in {".csv", ".json", ".jsonl", ".xlsx"}:
            continue
        if "cursor" in key:
            continue
        seen.add(key)
        uniq.append(f)

    currency = None
    n_rows = 0
    usd_found = False
    cost_mgmt_found = False
    for f in uniq:
        entry: dict[str, Any] = {"path": _rel(f), "kind": f.suffix.lower()}
        name_l = f.name.lower()
        if f.suffix.lower() == ".json" and name_l.startswith("cost_query_"):
            cq = _ingest_cost_query_json(f)
            cost_queries.append(cq)
            entry["cost_query"] = {
                "ok": cq.get("ok"),
                "period": cq.get("period"),
                "cost_sum": cq.get("cost_sum"),
                "currency": cq.get("currency"),
                "err": cq.get("err"),
            }
            if cq.get("ok") and cq.get("cost_readable"):
                cost_mgmt_found = True
                currency = cq.get("currency") or currency
                n_rows += len(cq.get("rows") or [])
        elif f.suffix.lower() == ".json" and "consumption_usage" in name_l:
            cons = _ingest_consumption_json(f)
            consumption.append(cons)
            entry["consumption"] = {
                "n_rows": cons.get("n_rows"),
                "cost_readable": cons.get("cost_readable"),
                "openai_accounts": cons.get("openai_accounts"),
            }
            if cons.get("cost_readable"):
                usd_found = True
                n_rows += int(cons.get("n_rows") or 0)
        elif f.suffix.lower() == ".csv":
            try:
                with f.open(encoding="utf-8-sig", newline="") as fh:
                    reader = csv.DictReader(fh)
                    cost_cols = [
                        c
                        for c in (reader.fieldnames or [])
                        if re.search(r"cost|amount|charge|usd|pretax", c, re.I)
                    ]
                    s = 0.0
                    n = 0
                    for row in reader:
                        n += 1
                        for c in cost_cols:
                            s += _fnum(row.get(c))
                    entry["rows"] = n
                    entry["parsed_usd"] = round(s, 6) if cost_cols else None
                    if cost_cols:
                        usd_found = True
                        n_rows += n
            except OSError:
                entry["err"] = "read_fail"
        hits.append(entry)

    # Dedupe periods: prefer resource-group queries; skip duplicate mtd if 2026-08_mtd exists
    by_period: list[dict[str, Any]] = []
    seen_period: set[str] = set()
    for c in sorted(cost_queries, key=lambda x: str(x.get("period") or "")):
        if not c.get("ok"):
            continue
        period = str(c.get("period") or "")
        if period in {"mtd", "mtd_resource"}:
            continue  # covered by 2026-08_mtd / retries
        if period in seen_period:
            continue
        seen_period.add(period)
        by_period.append(
            {
                "period": period,
                "cost_sum": c.get("cost_sum"),
                "currency": c.get("currency"),
                "rows": c.get("rows"),
                "path": c.get("path"),
            }
        )

    meters_only = bool(consumption) and not usd_found and not cost_mgmt_found
    if cost_mgmt_found:
        note = "Azure Cost Management ActualCost 조회 성공 (통화=응답 Currency)"
    elif usd_found:
        note = "청구/$ 합산 가능"
    elif meters_only:
        note = "Azure consumption usage JSON · pretaxCost=None → $합 불가"
    else:
        note = "data/acodeai/에 Azure·OpenAI 청구 없음"

    return {
        "found": usd_found or cost_mgmt_found,
        "cost_management_found": cost_mgmt_found,
        "meters_observed_without_usd": meters_only,
        "files": hits,
        "consumption_exports": consumption,
        "cost_management_queries": by_period,
        "currency": currency,
        "rows": n_rows,
        "note_ko": note,
        "openai_accounts_union": sorted(
            {a for c in consumption for a in (c.get("openai_accounts") or [])}
        ),
        "products_union": sorted({p for c in consumption for p in (c.get("products") or {})}),
    }


def _cache_delta_advisory(jsonl: Path) -> dict[str, Any]:
    if not jsonl.is_file():
        return {"ok": False, "err": f"missing {_rel(jsonl)}"}
    sum_c1 = sum_c2 = sum_save_c2 = 0.0
    sum_prompt = sum_cached = sum_out = 0
    n = 0
    sample_ids: list[Any] = []
    for line in jsonl.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        n += 1
        c1 = _usage_cost(row.get("azure_call1_usage"))
        c2 = _usage_cost(row.get("azure_call2_usage"))
        sum_c1 += c1["cost_usd_advisory"]
        sum_c2 += c2["cost_usd_advisory"]
        sum_save_c2 += c2["cache_saving_usd_advisory"]
        sum_prompt += int(c1["prompt_tokens"] + c2["prompt_tokens"])
        sum_cached += int(c1["cached_tokens"] + c2["cached_tokens"])
        sum_out += int(c1["completion_tokens"] + c2["completion_tokens"])
        if len(sample_ids) < 5:
            sample_ids.append(row.get("id"))
    return {
        "ok": True,
        "n_cases": n,
        "jsonl": _rel(jsonl),
        "price_sheet": ADVISORY_PRICE,
        "tokens": {
            "prompt_sum_call1_plus_call2": sum_prompt,
            "cached_sum_call1_plus_call2": sum_cached,
            "completion_sum_call1_plus_call2": sum_out,
        },
        "usd_advisory": {
            "call1_sum": round(sum_c1, 6),
            "call2_sum": round(sum_c2, 6),
            "pair_sum_call1_plus_call2": round(sum_c1 + sum_c2, 6),
            "call2_cache_saving_sum": round(sum_save_c2, 6),
            "mean_call2_cache_saving": round(sum_save_c2 / n, 8) if n else None,
        },
        "honesty_ko": (
            "캐시 델타 30건 → 공개 단가표로 $ 환산(advisory) 가능. "
            "≠ Azure 청구서 감소 증명 · ≠ commercial 47.5 SLA · SEND HOLD"
        ),
        "sample_ids_head": sample_ids,
    }


def main() -> int:
    as_of = _utc()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    billing = _scan_billing_exports(DATA_DIR)
    advisory = _cache_delta_advisory(SELF_TRAFFIC_JSONL)
    gate = _load(SELF_TRAFFIC_GATE)
    run = _load(SELF_TRAFFIC_RUN)
    cursor_v = _load(CURSOR_VERDICT)

    periods = billing.get("cost_management_queries") or []
    cost_mgmt = bool(billing.get("cost_management_found"))
    meters_only = bool(billing.get("meters_observed_without_usd"))
    currency = billing.get("currency") or "KRW"

    # Headline periods (exclude failed / duplicate)
    monthly_lines = []
    spend_nonzero = False
    for p in periods:
        cs = float(p.get("cost_sum") or 0)
        if cs > 0:
            spend_nonzero = True
        cur = p.get("currency") or currency
        usd_adv = None
        if cur == "KRW":
            usd_adv = round(cs / KRW_PER_USD_ADVISORY, 4)
        monthly_lines.append(
            {
                "period": p.get("period"),
                "cost": cs,
                "currency": cur,
                "usd_equiv_advisory": usd_adv,
                "rows": p.get("rows"),
            }
        )

    if cost_mgmt:
        plane_status = "MEASURED_COST_MGMT"
        # Spend exists ≠ automatic 「샌다」(waste). Commander decides leak vs intentional burn.
        verdict = "OPEN_지휘관칸"
        verdict_note = (
            f"Azure ActualCost 실측됨(통화={currency}). "
            "사용료 존재 ≠ 자동 '샌다'. 낭비/필수 dogfood 구분은 지휘관 칸. "
            f"Cache-Delta30 advisory 절감은 청구 대비 극소."
        )
        next_1 = (
            "지휘관 판정 칸: 외부 API 평면 샌다/안샌다 "
            "(의도적 dogfood burn vs 낭비). 선택: ResourceId 분해 재조회(429 해소 후)."
        )
    elif meters_only:
        plane_status = "METERS_WITHOUT_USD"
        verdict = "미측정(청구$)"
        verdict_note = "consumption 미터만 · pretaxCost=None"
        next_1 = "Cost Management ActualCost 재조회 또는 Portal CSV"
    elif billing.get("found"):
        plane_status = "MEASURED_INVOICE"
        verdict = "OPEN_지휘관칸"
        verdict_note = "청구 export 합산됨 · 샌다/안샌다 최종은 지휘관 칸"
        next_1 = "지휘관 판정 칸 기입"
    else:
        plane_status = "PROXY_ONLY_ADVISORY"
        verdict = "미측정(청구$)"
        verdict_note = "청구 없음 · advisory만"
        next_1 = "Azure Cost CSV / ActualCost 조회"

    usd = (advisory.get("usd_advisory") or {}) if advisory.get("ok") else {}
    art: dict[str, Any] = {
        "schema": "acodeai_external_api_spend_audit_onepager_v1",
        "generated_at_utc": as_of,
        "research_only": True,
        "send_gate": "HOLD",
        "pass_claimed": False,
        "product_all_ok": False,
        "cash_cow_proven": False,
        "lane": "ms",
        "plane": "external_api_usd",
        "plane_status": plane_status,
        "verdict_ko": verdict,
        "verdict_note_ko": verdict_note,
        "spend_nonzero": spend_nonzero,
        "cursor_plane_pointer": {
            "verdict": cursor_v.get("verdict"),
            "scope": cursor_v.get("verdict_scope_ko"),
            "path": _rel(CURSOR_VERDICT) if CURSOR_VERDICT.is_file() else None,
        },
        "billing_export": billing,
        "monthly_actual_cost": monthly_lines,
        "fx_advisory": {
            "krw_per_usd": KRW_PER_USD_ADVISORY,
            "note_ko": "표시용 환산만 · 청구 통화는 Cost Management Currency",
        },
        "providers": {
            "azure_openai_foundry": {
                "source": "Azure Cost Management ActualCost",
                "resource_group": "mkm-startups-rg",
                "account_hint": (billing.get("openai_accounts_union") or ["mkm-openai-eastus2"])[:3],
                "currency": currency,
                "monthly": monthly_lines,
                "dogfood_paid_calls_wrapped": run.get("paid_azure_calls"),
                "gate_decision": gate.get("gate_decision")
                or (gate.get("summary") or {}).get("gate_decision"),
                "mean_delta": gate.get("mean_delta")
                or (gate.get("summary") or {}).get("mean_delta"),
            },
            "openai_direct": {
                "invoice": None,
                "note_ko": "직접 OpenAI 청구 export 없음",
            },
        },
        "cache_delta_30_usd_conversion": advisory,
        "walls_ko": [
            "ActualCost(KRW) ≠ Cache-Delta advisory USD",
            "사용료>0 ≠ 자동 '샌다'(낭비)",
            "stub/proxy saving ≠ commercial 47.5",
            "Cursor 안 샌다 ≠ 외부 API 안 샌다",
            "≠ cash_cow_proven · ≠ SEND · research_only",
        ],
        "gap_ko": [
            "2026-05 Cost query 429로 미수집",
            "ResourceId 분해 429",
            "OpenAI 직접 청구 미입고",
            "Cache-Delta30 advisory 절감 vs 월 ActualCost 스케일 불일치",
        ],
        "next_1": next_1,
        "reproduce": "py scripts/run_acodeai_external_api_spend_audit_onepager_v1.py",
        "center_locked_next_1": (_load(CENTER) or {}).get("locked_next_1"),
    }

    OUT_JSON.write_text(json.dumps(art, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    month_md = []
    for m in monthly_lines:
        usd_e = m.get("usd_equiv_advisory")
        usd_s = f" (~${usd_e} advisory)" if usd_e is not None else ""
        month_md.append(
            f"- **{m.get('period')}:** {m.get('cost'):,.4f} {m.get('currency')}{usd_s}"
        )

    md = "\n".join(
        [
            "# a-codeai External API $ Spend Audit — 1장",
            "",
            f"- **as_of:** `{as_of}`",
            "- **research_only · SEND HOLD · product_all_ok=false · cash_cow_proven=false**",
            f"- **plane_status:** `{plane_status}`",
            f"- **판정(외부 API $):** `{verdict}` — {verdict_note}",
            f"- **spend_nonzero:** `{spend_nonzero}`",
            "",
            "## Cursor 평면 (이미 스탬프)",
            f"- {cursor_v.get('verdict')} · {cursor_v.get('verdict_scope_ko')}",
            "",
            "## Azure ActualCost (Cost Management)",
            f"- note: {billing.get('note_ko')}",
            f"- RG: `mkm-startups-rg` · accounts: `{billing.get('openai_accounts_union')}`",
            *month_md,
            "",
            "## Cache-Delta 30건 → $ 환산 (advisory)",
            f"- n: `{advisory.get('n_cases')}`",
            f"- pair_sum USD advisory: `{usd.get('pair_sum_call1_plus_call2')}`",
            f"- call2 cache saving USD advisory: `{usd.get('call2_cache_saving_sum')}`",
            f"- honesty: {advisory.get('honesty_ko')}",
            "",
            "## NEXT-1",
            art["next_1"],
            "",
            f"artifact: `{_rel(OUT_JSON)}`",
            "",
        ]
    )
    OUT_MD.write_text(md, encoding="utf-8")

    # elementary one-liner with biggest recent month
    latest = monthly_lines[-1] if monthly_lines else {}
    PASTE.parent.mkdir(parents=True, exist_ok=True)
    PASTE.write_text(
        "\n".join(
            [
                "research_only · SEND HOLD · product_all_ok=false · harness≠product · pass_claimed=false",
                "",
                (
                    f"한줄: 외부 API ActualCost 실측 · "
                    f"{latest.get('period')}={latest.get('cost')} {latest.get('currency')} · "
                    f"판정칸 OPEN · CacheΔ30 advisory 절감 ${usd.get('call2_cache_saving_sum')}"
                ),
                f"된것: Cost Mgmt 월합 + onepager {_rel(OUT_MD)} · advisory $ 환산",
                "안된것: 지휘관 샌다/안샌다 · cash_cow · SEND · OpenAI direct · May/ResourceId",
                f"다음1타: {art['next_1']}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "ok": True,
                "plane_status": plane_status,
                "verdict_ko": verdict,
                "monthly": [
                    {"period": m["period"], "cost": m["cost"], "currency": m["currency"]}
                    for m in monthly_lines
                ],
                "advisory_call2_saving_usd": usd.get("call2_cache_saving_sum"),
                "json": _rel(OUT_JSON),
                "md": _rel(OUT_MD),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
