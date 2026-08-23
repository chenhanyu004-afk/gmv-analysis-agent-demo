from app.analyzer import analyze


def test_detects_large_decline_and_top_channel():
    result = analyze({
        "rows": [
            {"channel": "直播", "live_room_id": "room-1", "anchor_id": "a-1", "sku_id": "sku-1", "gmv_paid": 60000, "baseline_gmv_paid": 110000, "paying_buyers": 600, "baseline_paying_buyers": 1000, "orders_paid": 650, "baseline_orders_paid": 1100, "stock": 0},
            {"channel": "商城", "live_room_id": None, "anchor_id": None, "sku_id": "sku-2", "gmv_paid": 40000, "baseline_gmv_paid": 50000, "paying_buyers": 400, "baseline_paying_buyers": 500, "orders_paid": 420, "baseline_orders_paid": 520},
        ],
        "data_freshness": "2026-08-23 11:05",
    })
    assert result["alert"]["triggered"] is True
    assert result["alert"]["level"] == "P1"
    assert result["top_contributors"]["channel"][0]["channel"] == "直播"
