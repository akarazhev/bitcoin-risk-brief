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

from app.brief import SUPPORTED_BRIEF_LOCALES, build_brief
from app.config import settings
from app.db import connect, disconnect, get_pool
from app.repository import (
    fetch_latest_brief,
    fetch_latest_risk,
    fetch_latest_risk_level_snapshot,
    fetch_latest_validation,
    fetch_ohlcv_history,
    fetch_previous_risk,
    fetch_public_data_version,
    fetch_risk_history,
    upsert_waitlist_lead,
)
from app.public_cache import (
    PublicCacheWarmupResult,
    PublicCacheWarmupTarget,
    PublicEndpointCache,
    build_cache_headers,
    etag_matches,
    no_store_headers,
    warm_public_endpoint_cache,
)
from app.rate_limit import FixedWindowRateLimiter
from app.readiness import build_readiness_payload
from app.risk_levels import build_risk_levels, build_risk_levels_public_payload
from app.security import build_security_headers
from app.turnstile import TurnstileRejected, TurnstileUnavailable, verify_turnstile_token
from app.waitlist import InvalidWaitlistContact


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await connect()
    global logger
    logger = _configure_access_logger()
    try:
        await warm_public_read_cache_on_startup()
    except Exception:
        logger.exception("public_cache_warmup_failed phase=startup")
    try:
        yield
    finally:
        await disconnect()


class WaitlistRequest(BaseModel):
    contact: str = Field(min_length=3, max_length=254)
    locale: str = Field(default="en")
    source: str = Field(default="landing", max_length=64)
    turnstile_token: str = Field(min_length=1, max_length=2048)


app = FastAPI(
    title="Bitcoin Risk Brief API",
    version="0.1.0",
    description=(
        "A daily Bitcoin risk signal computed from canonical BTC/USD daily data. "
        "Call GET /api/readiness before reporting any value: it returns HTTP 503 when data is stale or "
        "validation failed, and a risk number without its freshness state is not usable. "
        "This is analytics and research context, not financial advice, not a price forecast, and not a trade signal."
    ),
    openapi_url="/api/openapi.json",
    docs_url=None,
    redoc_url=None,
    servers=[{"url": "https://bitcoinriskbrief.minihub.app", "description": "Production"}],
    lifespan=lifespan,
)


def _configure_access_logger() -> logging.Logger:
    access_logger = logging.getLogger("app.access")
    access_logger.setLevel(logging.INFO)

    uvicorn_logger = logging.getLogger("uvicorn.error")
    handlers = uvicorn_logger.handlers or logging.getLogger("uvicorn").handlers
    if handlers:
        for handler in handlers:
            if handler not in access_logger.handlers:
                access_logger.addHandler(handler)
        access_logger.propagate = False

    return access_logger


logger = _configure_access_logger()
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


async def _produce_readiness_payload() -> tuple[dict[str, Any], int]:
    pool = get_pool()
    latest = await fetch_latest_risk(pool)
    validation = await fetch_latest_validation(pool)
    return build_readiness_payload(
        latest,
        validation,
        max_age_days=settings.data_freshness_max_age_days,
    )


async def _produce_risk_latest_payload() -> tuple[dict[str, Any], int]:
    latest = await fetch_latest_risk(get_pool())
    if latest is None:
        raise HTTPException(status_code=404, detail="Risk data has not been collected yet")
    return {"data": latest}, 200


def _risk_history_producer(
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 2000,
) -> Callable[[], Awaitable[tuple[dict[str, Any], int]]]:
    async def producer() -> tuple[dict[str, Any], int]:
        rows = await fetch_risk_history(get_pool(), start_date=start_date, end_date=end_date, limit=limit)
        return {"data": rows, "meta": {"returned_points": len(rows)}}, 200

    return producer


async def _produce_risk_levels_payload() -> tuple[dict[str, Any], int]:
    pool = get_pool()
    persisted = await fetch_latest_risk_level_snapshot(pool)
    if persisted is not None:
        return persisted, 200

    latest = await fetch_latest_risk(pool)
    source_rows = await fetch_ohlcv_history(pool)
    if latest is None or len(source_rows) < 2:
        raise HTTPException(status_code=404, detail="Risk source data has not been collected yet")

    turnover_enabled = bool(latest["turnover_enabled"])
    levels = build_risk_levels(source_rows, {"turnover_enabled": turnover_enabled})
    return build_risk_levels_public_payload(
        latest=latest,
        levels=levels,
        source_row_count=len(source_rows),
    ), 200


def _brief_has_supported_locales(payload: dict[str, Any]) -> bool:
    sections = payload.get("sections")
    return isinstance(sections, dict) and set(SUPPORTED_BRIEF_LOCALES).issubset(sections)


async def _produce_brief_latest_payload() -> tuple[dict[str, Any], int]:
    pool = get_pool()
    persisted = await fetch_latest_brief(pool)
    if persisted is not None and _brief_has_supported_locales(persisted):
        return {"data": persisted}, 200
    latest = await fetch_latest_risk(pool)
    if latest is None:
        if persisted is not None:
            return {"data": persisted}, 200
        raise HTTPException(status_code=404, detail="Brief data has not been collected yet")
    previous = await fetch_previous_risk(pool)
    return {"data": build_brief(latest, previous)}, 200


def _standard_public_cache_warmup_targets() -> tuple[PublicCacheWarmupTarget, ...]:
    return (
        PublicCacheWarmupTarget("GET /api/risk/latest", _produce_risk_latest_payload),
        PublicCacheWarmupTarget("GET /api/risk/history?limit=730", _risk_history_producer(limit=730)),
        PublicCacheWarmupTarget("GET /api/risk/levels", _produce_risk_levels_payload),
        PublicCacheWarmupTarget("GET /api/brief/latest", _produce_brief_latest_payload),
    )


async def warm_public_read_cache_on_startup() -> PublicCacheWarmupResult:
    data_version = await fetch_public_data_version(get_pool())
    if data_version == "validation:empty":
        logger.info("public_cache_warmup_skipped reason=no_validation")
        return PublicCacheWarmupResult((), ())

    try:
        readiness_payload, readiness_status = await _produce_readiness_payload()
    except Exception:
        logger.exception("public_cache_warmup_skipped reason=readiness_probe_failed")
        return PublicCacheWarmupResult((), ())

    if readiness_status != 200:
        logger.warning(
            "public_cache_warmup_skipped reason=readiness_not_ready status=%d payload_status=%s",
            readiness_status,
            readiness_payload.get("status"),
        )
        return PublicCacheWarmupResult((), ())

    result = await warm_public_endpoint_cache(
        public_read_cache,
        data_version,
        _standard_public_cache_warmup_targets(),
        logger=logger,
    )
    logger.info(
        "public_cache_warmup_complete warmed=%d failed=%d duration_ms=%.1f slowest=%s",
        len(result.warmed_keys),
        len(result.failed_keys),
        result.total_duration_ms,
        result.slowest_summary(),
    )
    return result


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


@app.get(
    "/api/health",
    tags=["status"],
    summary="Service health",
    description="Returns the service health status for deployment probes. This is not financial advice.",
)
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/api/readiness",
    tags=["status"],
    summary="Freshness and validation state",
    description=(
        "Returns HTTP 200 when every check passes and HTTP 503 when the data is stale or validation failed. "
        "Never cached. Call this before reporting any risk value. This is not financial advice."
    ),
)
async def readiness() -> Response:
    payload, status_code = await _produce_readiness_payload()
    return JSONResponse(status_code=status_code, content=payload, headers=no_store_headers())


@app.get(
    "/api/risk/latest",
    tags=["risk"],
    summary="Latest Bitcoin risk signal",
    description=(
        "Returns the latest completed daily Bitcoin risk point and its model context. "
        "Call GET /api/readiness first to confirm the data is usable. This is not financial advice."
    ),
)
async def risk_latest(request: Request) -> Response:
    return await _cached_public_json_response(request, _produce_risk_latest_payload)


@app.get(
    "/api/risk/history",
    tags=["risk"],
    summary="Historical Bitcoin risk signals",
    description=(
        "Returns completed daily Bitcoin risk rows in ascending timestamp order. "
        "Call GET /api/readiness first to confirm the data is usable. This is not financial advice."
    ),
)
async def risk_history(
    request: Request,
    start_date: Annotated[date | None, Query(description="Start date YYYY-MM-DD")] = None,
    end_date: Annotated[date | None, Query(description="End date YYYY-MM-DD")] = None,
    limit: Annotated[int, Query(ge=2, le=5000)] = 2000,
) -> Response:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be earlier than end_date")

    return await _cached_public_json_response(
        request,
        _risk_history_producer(start_date=start_date, end_date=end_date, limit=limit),
    )


@app.get(
    "/api/risk/levels",
    tags=["risk"],
    summary="Bitcoin risk-level price scenarios",
    description=(
        "Returns model-solved price scenarios for each risk level. "
        "These outputs are not forecasts, targets, or trading instructions. This is not financial advice."
    ),
)
async def risk_levels(request: Request) -> Response:
    return await _cached_public_json_response(request, _produce_risk_levels_payload)


@app.get(
    "/api/brief/latest",
    tags=["brief"],
    summary="Latest daily Bitcoin brief",
    description=(
        "Returns the latest daily Bitcoin risk brief in the supported locales. "
        "Call GET /api/readiness first to confirm the data is usable. This is not financial advice."
    ),
)
async def brief_latest(request: Request) -> Response:
    return await _cached_public_json_response(request, _produce_brief_latest_payload)


@app.post(
    "/api/waitlist",
    status_code=201,
    tags=["waitlist"],
    summary="Join the Bitcoin Risk Brief waitlist",
    description=(
        "Stores a submitted email address or Telegram handle after Turnstile verification. "
        "This is not financial advice."
    ),
)
async def waitlist_join(payload: WaitlistRequest) -> JSONResponse:
    try:
        await verify_turnstile_token(
            payload.turnstile_token,
            secret=settings.turnstile_secret,
            expected_hostnames=settings.turnstile_hostnames,
        )
    except TurnstileRejected as exc:
        raise HTTPException(status_code=403, detail="Turnstile verification failed") from exc
    except TurnstileUnavailable as exc:
        raise HTTPException(status_code=503, detail="Turnstile verification unavailable") from exc

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
