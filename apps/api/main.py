from __future__ import annotations

from fastapi import FastAPI

from apps.api.deps import get_mode, is_demo_mode
from apps.api.routers.markets import router as markets_router
from apps.api.routers.regime import router as regime_router
from apps.api.routers.research import router as research_router
from apps.api.routers.screener import router as screener_router

app = FastAPI(
    title="Meridian API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(research_router, prefix="/api/v1")
app.include_router(screener_router, prefix="/api/v1")
app.include_router(regime_router, prefix="/api/v1")
app.include_router(markets_router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "mode": get_mode(),
        "version": "0.1.0",
    }


@app.get("/api/v1/metadata")
async def metadata() -> dict[str, object]:
    return {
        "version": "0.1.0",
        "model": "glm-5.1",
        "demo": is_demo_mode(),
        "data_sources": ["fred", "kalshi", "polymarket", "edgar", "news"],
    }
