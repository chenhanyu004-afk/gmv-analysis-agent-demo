from __future__ import annotations

from collections import defaultdict
from typing import Any


def _pct(current: float, baseline: float) -> float | None:
    if baseline == 0:
        return None
    return (current - baseline) / baseline


def _level(change: float | None, threshold: float) -> str:
    if change is None or abs(change) < threshold:
        return "P2"
    if change <= -0.40:
        return "P0"
    if change <= -0.20:
        return "P1"
    return "P2"


def _contributions(rows: list[dict[str, Any]], dimension: str) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, float]] = defaultdict(lambda: {"current": 0.0, "baseline": 0.0})
    for row in rows:
        key = str(row.get(dimension) or "未归类")
        grouped[key]["current"] += float(row.get("gmv_paid", 0))
        grouped[key]["baseline"] += float(row.get("baseline_gmv_paid", 0))
    result = [
        {
            dimension: key,
            "current_gmv": round(values["current"], 2),
            "baseline_gmv": round(values["baseline"], 2),
            "delta_gmv": round(values["current"] - values["baseline"], 2),
        }
        for key, values in grouped.items()
    ]
    return sorted(result, key=lambda item: abs(item["delta_gmv"]), reverse=True)


def analyze(payload: dict[str, Any]) -> dict[str, Any]:
    """Diagnose a current-period GMV anomaly from pre-aggregated fact rows."""
    rows = payload.get("rows", [])
    config = payload.get("config", {})
    threshold = float(config.get("relative_threshold", 0.20))
    absolute_threshold = float(config.get("absolute_threshold", 5000))
    current_gmv = sum(float(row.get("gmv_paid", 0)) for row in rows)
    baseline_gmv = sum(float(row.get("baseline_gmv_paid", 0)) for row in rows)
    delta_gmv = current_gmv - baseline_gmv
    relative_change = _pct(current_gmv, baseline_gmv)
    triggered = bool(relative_change is not None and abs(relative_change) >= threshold and abs(delta_gmv) >= absolute_threshold)

    current_buyers = sum(float(row.get("paying_buyers", 0)) for row in rows)
    baseline_buyers = sum(float(row.get("baseline_paying_buyers", 0)) for row in rows)
    current_orders = sum(float(row.get("orders_paid", 0)) for row in rows)
    baseline_orders = sum(float(row.get("baseline_orders_paid", 0)) for row in rows)
    current_items = sum(float(row.get("items_paid", row.get("orders_paid", 0))) for row in rows)
    baseline_items = sum(float(row.get("baseline_items_paid", row.get("baseline_orders_paid", 0))) for row in rows)
    factors = {
        "支付买家数": {"current": current_buyers, "baseline": baseline_buyers, "change": _pct(current_buyers, baseline_buyers)},
        "人均支付件数": {"current": current_items / current_buyers if current_buyers else 0, "baseline": baseline_items / baseline_buyers if baseline_buyers else 0},
        "客单价": {"current": current_gmv / current_orders if current_orders else 0, "baseline": baseline_gmv / baseline_orders if baseline_orders else 0},
    }
    for item in factors.values():
        item["change"] = _pct(item["current"], item["baseline"])
        item["current"] = round(item["current"], 4)
        item["baseline"] = round(item["baseline"], 4)

    scopes = {key: _contributions(rows, key)[:5] for key in ("channel", "live_room_id", "anchor_id", "sku_id")}
    health_rows = [row for row in rows if float(row.get("stock", 1)) <= 0 or float(row.get("late_dispatch_rate", 0)) >= 0.10]
    root_causes: list[dict[str, Any]] = []
    for scope, values in scopes.items():
        if values and abs(values[0]["delta_gmv"]) >= max(abs(delta_gmv) * 0.15, 1):
            root_causes.append({"confidence": "高", "hypothesis": f"{scope} 维度的 {values[0][scope]} 是主要波动来源", "impact_gmv": values[0]["delta_gmv"], "evidence": values[0]})
    if health_rows:
        root_causes.append({"confidence": "中", "hypothesis": "库存或履约健康度异常，可能抑制支付转化", "impact_gmv": None, "evidence": {"affected_rows": len(health_rows)}})

    actions = []
    if delta_gmv < 0:
        actions = ["30分钟内：核对异常对象的开播、库存、价格、优惠与支付链路状态。", "当日：为主波动对象设置库存、开播时长和转化率告警。"]
    elif delta_gmv > 0:
        actions = ["30分钟内：确认增长是否来自可持续流量或活动，避免库存断供。", "当日：复盘高贡献渠道/SKU，评估加投或复制直播排期。"]

    return {
        "alert": {
            "triggered": triggered,
            "level": _level(relative_change, threshold) if triggered else "无预警",
            "current_gmv": round(current_gmv, 2),
            "baseline_gmv": round(baseline_gmv, 2),
            "delta_gmv": round(delta_gmv, 2),
            "relative_change": round(relative_change, 4) if relative_change is not None else None,
            "data_freshness": payload.get("data_freshness", "未提供"),
        },
        "factor_decomposition": factors,
        "top_contributors": scopes,
        "root_causes": root_causes[:3],
        "recommended_actions": actions,
        "data_quality_note": "请确认当前期与基线期采用相同支付GMV口径，并使用同星期同小时或活动日基线。",
    }
