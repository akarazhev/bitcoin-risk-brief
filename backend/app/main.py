from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.brief import build_brief
from app.config import settings
from app.db import connect, disconnect, get_pool
from app.repository import (
    fetch_latest_brief,
    fetch_latest_risk,
    fetch_ohlcv_history,
    fetch_previous_risk,
    fetch_risk_history,
    upsert_waitlist_lead,
)
from app.risk import METHODOLOGY_VERSION
from app.risk_levels import build_risk_levels
from app.waitlist import InvalidWaitlistContact


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await connect()
    try:
        yield
    finally:
        await disconnect()


class WaitlistRequest(BaseModel):
    contact: str = Field(min_length=3, max_length=254)
    locale: str = Field(default="en", max_length=8)
    source: str = Field(default="landing", max_length=64)


app = FastAPI(title="Bitcoin Risk Brief API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/risk/latest")
async def risk_latest() -> dict[str, Any]:
    latest = await fetch_latest_risk(get_pool())
    if latest is None:
        raise HTTPException(status_code=404, detail="Risk data has not been collected yet")
    return {"data": latest}


@app.get("/api/risk/history")
async def risk_history(
    start_date: Annotated[date | None, Query(description="Start date YYYY-MM-DD")] = None,
    end_date: Annotated[date | None, Query(description="End date YYYY-MM-DD")] = None,
    limit: Annotated[int, Query(ge=2, le=5000)] = 2000,
) -> dict[str, Any]:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be earlier than end_date")
    rows = await fetch_risk_history(get_pool(), start_date=start_date, end_date=end_date, limit=limit)
    return {"data": rows, "meta": {"returned_points": len(rows)}}


@app.get("/api/risk/levels")
async def risk_levels() -> dict[str, Any]:
    pool = get_pool()
    latest = await fetch_latest_risk(pool)
    source_rows = await fetch_ohlcv_history(pool)
    if latest is None or len(source_rows) < 2:
        raise HTTPException(status_code=404, detail="Risk source data has not been collected yet")

    turnover_enabled = all(row["volume"] > 0 and row["market_cap"] > 0 for row in source_rows)
    levels = build_risk_levels(source_rows, {"turnover_enabled": turnover_enabled})
    return {
        "data": [
            {"risk": row["risk"], "price_usd": round(row["price"], 2)}
            for row in levels["risk_level_rows"]
        ],
        "meta": {
            "base": latest,
            "methodology_version": METHODOLOGY_VERSION,
            "evaluation_date": levels["evaluation_date"].isoformat(),
            "current_price": levels["current_price"],
            "current_risk": levels["current_risk"],
            "turnover_enabled": levels["turnover_enabled"],
            "risk_step": 0.025,
            "source_row_count": len(source_rows),
        },
    }


@app.get("/api/brief/latest")
async def brief_latest() -> dict[str, Any]:
    pool = get_pool()
    persisted = await fetch_latest_brief(pool)
    if persisted is not None:
        return {"data": persisted}
    latest = await fetch_latest_risk(pool)
    if latest is None:
        raise HTTPException(status_code=404, detail="Brief data has not been collected yet")
    previous = await fetch_previous_risk(pool)
    return {"data": build_brief(latest, previous)}


@app.post("/api/waitlist", status_code=201)
async def waitlist_join(payload: WaitlistRequest) -> dict[str, Any]:
    try:
        lead = await upsert_waitlist_lead(
            get_pool(),
            contact=payload.contact,
            locale=payload.locale,
            source=payload.source,
        )
    except InvalidWaitlistContact as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "data": {
            "contact_type": lead["contact_type"],
            "locale": lead["locale"],
            "created": lead["created"],
        }
    }

