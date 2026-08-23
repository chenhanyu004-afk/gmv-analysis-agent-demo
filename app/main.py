from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.analyzer import analyze

app = FastAPI(title="Douyin GMV Anomaly Agent", version="0.1.0")


class AnalysisRequest(BaseModel):
    rows: list[dict[str, Any]] = Field(min_length=1, description="当前期与基线期的小时级事实行")
    data_freshness: str = "未提供"
    config: dict[str, float] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
def run_analysis(request: AnalysisRequest) -> dict[str, Any]:
    try:
        return analyze(request.model_dump())
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=f"数据格式错误：{error}") from error
