from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"


def _date_from_millis(timestamp_ms: float | int) -> datetime:
    return datetime.fromtimestamp(float(timestamp_ms) / 1000, tz=timezone.utc)


def _series_to_map(rows: list[list[float]]) -> dict[datetime.date, float]:
    mapped: dict[datetime.date, float] = {}
    for timestamp_ms, value in rows:
        mapped[_date_from_millis(timestamp_ms).date()] = float(value)
    return mapped


def market_chart_to_daily_rows(payload: dict[str, list[list[float]]]) -> list[dict[str, Any]]:
    prices = _series_to_map(payload.get("prices", []))
    market_caps = _series_to_map(payload.get("market_caps", []))
    volumes = _series_to_map(payload.get("total_volumes", []))
    days = sorted(set(prices) & set(market_caps) & set(volumes))
    rows: list[dict[str, Any]] = []
    for day in days:
        close = prices[day]
        market_cap = market_caps[day]
        volume = volumes[day]
        supply = market_cap / close if close > 0 else 0.0
        rows.append(
            {
                "date": day,
                "open": close,
                "high": close,
                "low": close,
                "close": close,
                "volume": volume,
                "market_cap": market_cap,
                "circulating_supply": supply,
            }
        )
    return rows


class CoinGeckoClient:
    def __init__(self, *, api_key: str | None = None, timeout: float = 30.0) -> None:
        self.api_key = api_key.strip() if api_key else None
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}
        return {"x-cg-demo-api-key": self.api_key}

    async def fetch_bitcoin_market_chart(self, *, days: str) -> dict[str, list[list[float]]]:
        import httpx

        async with httpx.AsyncClient(base_url=COINGECKO_BASE_URL, timeout=self.timeout, headers=self._headers()) as client:
            response = await client.get(
                "/coins/bitcoin/market_chart",
                params={"vs_currency": "usd", "days": days, "interval": "daily"},
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("CoinGecko market_chart response must be an object")
            return payload
