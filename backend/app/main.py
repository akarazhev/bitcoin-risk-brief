from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date
import logging
import time
from typing import Annotated, Any, Awaitable, Callable

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.brief import build_brief
from app.config import settings
from app.db import connect, disconnect, get_pool
from app.repository import (
    fetch_latest_brief,
    fetch_latest_risk,
    fetch_latest_validation,
    fetch_ohlcv_history,
    fetch_previous_risk,
    fetch_public_data_version,
    fetch_risk_history,
    upsert_waitlist_lead,
)
from app.public_cache import (
    PublicEndpointCache,
    build_cache_headers,
    etag_matches,
    no_store_headers,
)
from app.rate_limit import FixedWindowRateLimiter
from app.readiness import build_readiness_payload
from app.risk import METHODOLOGY_VERSION
from app.risk_levels import build_risk_levels
from app.security import build_security_headers
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
logger = logging.getLogger("app.access")
waitlist_rate_limiter = FixedWindowRateLimiter(
    limit=max(1, settings.waitlist_rate_limit_per_hour),
    window_seconds=3600,
)
public_read_cache = PublicEndpointCache(ttl_seconds=settings.public_cache_ttl_seconds)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _client_key(request) -> str:
    cloudflare_ip = request.headers.get("cf-connecting-ip")
    if cloudflare_ip:
        return cloudflare_ip.strip()
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _public_cache_key(request: Request) -> str:
    query = request.url.query
    return f"{request.method} {request.url.path}?{query}" if query else f"{request.method} {request.url.path}"


async def _cached_public_json_response(
    request: Request,
    producer: Callable[[], Awaitable[tuple[dict[str, Any], int]]],
) -> Response:
    data_version = await fetch_public_data_version(get_pool())
    entry, cache_hit = await public_read_cache.get_or_build(
        _public_cache_key(request),
        data_version,
        producer,
    )
    headers = build_cache_headers(
        etag=entry.etag,
        data_version=entry.data_version,
        cache_hit=cache_hit,
        max_age_seconds=settings.public_cache_max_age_seconds,
        stale_while_revalidate_seconds=settings.public_cache_stale_while_revalidate_seconds,
    )
    if etag_matches(entry.etag, request.headers.get("if-none-match")):
        return Response(status_code=304, headers=headers)
    return JSONResponse(status_code=entry.status_code, content=entry.content, headers=headers)


@app.middleware("http")
async def waitlist_rate_limit_middleware(request, call_next):
    if request.method == "POST" and request.url.path == "/api/waitlist":
        if not waitlist_rate_limiter.allow(_client_key(request), now=time.time()):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many waitlist requests"},
                headers=no_store_headers(),
            )
        response = await call_next(request)
        for header_name, header_value in no_store_headers().items():
            response.headers[header_name] = header_value
        return response
    return await call_next(request)


@app.middleware("http")
async def security_headers_middleware(request, call_next):
    response = await call_next(request)
    for header_name, header_value in build_security_headers(app_env=settings.app_env).items():
        response.headers.setdefault(header_name, header_value)
    return response


@app.middleware("http")
async def api_access_log_middleware(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "api_request method=%s path=%s status=%d client=%s cf_ray=%s cache=%s duration_ms=%.1f",
            request.method,
            request.url.path,
            response.status_code,
            _client_key(request),
            request.headers.get("cf-ray", "-"),
            response.headers.get("X-Cache", "-"),
            duration_ms,
        )
    return response


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/readiness")
async def readiness(request: Request) -> Response:
    async def producer() -> tuple[dict[str, Any], int]:
        pool = get_pool()
        latest = await fetch_latest_risk(pool)
        validation = await fetch_latest_validation(pool)
        return build_readiness_payload(
            latest,
            validation,
            max_age_days=settings.data_freshness_max_age_days,
        )

    return await _cached_public_json_response(request, producer)


@app.get("/api/risk/latest")
async def risk_latest(request: Request) -> Response:
    async def producer() -> tuple[dict[str, Any], int]:
        latest = await fetch_latest_risk(get_pool())
        if latest is None:
            raise HTTPException(status_code=404, detail="Risk data has not been collected yet")
        return {"data": latest}, 200

    return await _cached_public_json_response(request, producer)


@app.get("/api/risk/history")
async def risk_history(
    request: Request,
    start_date: Annotated[date | None, Query(description="Start date YYYY-MM-DD")] = None,
    end_date: Annotated[date | None, Query(description="End date YYYY-MM-DD")] = None,
    limit: Annotated[int, Query(ge=2, le=5000)] = 2000,
) -> Response:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be earlier than end_date")

    async def producer() -> tuple[dict[str, Any], int]:
        rows = await fetch_risk_history(get_pool(), start_date=start_date, end_date=end_date, limit=limit)
        return {"data": rows, "meta": {"returned_points": len(rows)}}, 200

    return await _cached_public_json_response(request, producer)


@app.get("/api/risk/levels")
async def risk_levels(request: Request) -> Response:
    async def producer() -> tuple[dict[str, Any], int]:
        pool = get_pool()
        latest = await fetch_latest_risk(pool)
        source_rows = await fetch_ohlcv_history(pool)
        if latest is None or len(source_rows) < 2:
            raise HTTPException(status_code=404, detail="Risk source data has not been collected yet")

        turnover_enabled = bool(latest["turnover_enabled"])
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
        }, 200

    return await _cached_public_json_response(request, producer)


@app.get("/api/brief/latest")
async def brief_latest(request: Request) -> Response:
    async def producer() -> tuple[dict[str, Any], int]:
        pool = get_pool()
        persisted = await fetch_latest_brief(pool)
        if persisted is not None:
            return {"data": persisted}, 200
        latest = await fetch_latest_risk(pool)
        if latest is None:
            raise HTTPException(status_code=404, detail="Brief data has not been collected yet")
        previous = await fetch_previous_risk(pool)
        return {"data": build_brief(latest, previous)}, 200

    return await _cached_public_json_response(request, producer)


@app.post("/api/waitlist", status_code=201)
async def waitlist_join(payload: WaitlistRequest) -> JSONResponse:
    try:
        lead = await upsert_waitlist_lead(
            get_pool(),
            contact=payload.contact,
            locale=payload.locale,
            source=payload.source,
        )
    except InvalidWaitlistContact as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return JSONResponse(
        status_code=201,
        content={
            "data": {
                "contact_type": lead["contact_type"],
                "locale": lead["locale"],
                "created": lead["created"],
            }
        },
        headers=no_store_headers(),
    )
