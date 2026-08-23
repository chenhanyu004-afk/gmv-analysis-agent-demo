# 抖音 GMV 异动分析 Agent

用于抖音电商经营诊断的轻量 Agent：识别 GMV 异动，拆解支付买家数、件单数和客单价，并定位渠道、直播间、达人与 SKU 的波动贡献。

## 面试演示（推荐）

启动服务后，直接打开：

```
http://127.0.0.1:8000/
```

页面会加载一组**合成数据**，模拟「直播间开播不足 + SKU 缺货」导致的 GMV 下滑。点击“重新运行分析”即可现场展示预警、归因和运营动作。

## 启动

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

API 文档：`http://127.0.0.1:8000/docs`

## 接入真实数据

向 `POST /analyze` 提交小时级的当前期与基线期数据。核心字段包括：

- `gmv_paid` / `baseline_gmv_paid`
- `paying_buyers` / `baseline_paying_buyers`
- `orders_paid` / `baseline_orders_paid`
- `channel`、`live_room_id`、`anchor_id`、`sku_id`
- `stock`、`late_dispatch_rate`

默认告警条件为：相对变化达到 20%，且 GMV 绝对变化达到 5,000 元。可在请求的 `config` 中调整。
