from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.analyzer import analyze

app = FastAPI(title="Douyin GMV Anomaly Agent", version="0.2.0")
DEMO_PAGE = Path(__file__).with_name("demo.html")


class AnalysisRequest(BaseModel):
    rows: list[dict[str, Any]] = Field(min_length=1, description="当前期与基线期的小时级事实行")
    data_freshness: str = "未提供"
    config: dict[str, float] = {}


@app.get("/", include_in_schema=False)
def interview_demo() -> FileResponse:
    """A synthetic dashboard for interviewer demonstrations."""
    return FileResponse(DEMO_PAGE)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
def run_analysis(request: AnalysisRequest) -> dict[str, Any]:
    try:
        return analyze(request.model_dump())
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=f"数据格式错误：{error}") from error
