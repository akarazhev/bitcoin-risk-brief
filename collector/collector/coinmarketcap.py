from __future__ import annotations

import asyncio
from datetime import date, datetime
from typing import Any, Awaitable, Callable, Protocol

CMC_BASE_URL = "https://pro-api.coinmarketcap.com"
TRANSIENT_STATUS_CODES = {408, 409, 425, 429}


class CoinMarketCapError(RuntimeError):
    pass


class CoinMarketCapTransientError(CoinMarketCapError):
    pass


class CoinMarketCapPermanentError(CoinMarketCapError):
    pass


class CoinMarketCapTransport(Protocol):
    async def get_json(self, *, base_url: str, timeout: float, headers: dict[str, str], params: dict[str, Any]) -> dict[str, Any]:
        ...


class HttpxCoinMarketCapTransport:
    async def get_json(self, *, base_url: str, timeout: float, headers: dict[str, str], params: dict[str, Any]) -> dict[str, Any]:
        import httpx

        try:
            async with httpx.AsyncClient(base_url=base_url, timeout=timeout) as client:
                response = await client.get(
                    "/v2/cryptocurrency/ohlcv/historical",
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            if status_code in TRANSIENT_STATUS_CODES or status_code >= 500:
                raise CoinMarketCapTransientError(f"CoinMarketCap transient HTTP {status_code}") from exc
            raise CoinMarketCapPermanentError(f"CoinMarketCap permanent HTTP {status_code}") from exc
        except httpx.RequestError as exc:
            raise CoinMarketCapTransientError(f"CoinMarketCap request failed: {exc}") from exc
        except ValueError as exc:
            raise CoinMarketCapPermanentError("CoinMarketCap response JSON is invalid") from exc

        if not isinstance(payload, dict):
            raise CoinMarketCapPermanentError("CoinMarketCap OHLCV response must be an object")
        return payload


def _parse_utc_date(value: str) -> date:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def _select_quotes_container(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("CoinMarketCap OHLCV response must contain a data object")
    if isinstance(data.get("quotes"), list):
        return data["quotes"]
    for value in data.values():
        if isinstance(value, dict) and isinstance(value.get("quotes"), list):
            return value["quotes"]
    raise ValueError("CoinMarketCap OHLCV response does not contain quotes")


def cmc_ohlcv_payload_to_daily_rows(payload: dict[str, Any], *, convert: str = "USD") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for quote_row in _select_quotes_container(payload):
        quote = quote_row.get("quote", {}).get(convert)
        if not isinstance(quote, dict):
            raise ValueError(f"CoinMarketCap OHLCV row is missing {convert} quote")
        close = float(quote["close"])
        market_cap = float(quote["market_cap"])
        circulating_supply = market_cap / close if close > 0 else 0.0
        rows.append(
            {
                "date": _parse_utc_date(quote_row["time_open"]),
                "time_open": quote_row.get("time_open"),
                "time_close": quote_row.get("time_close"),
                "time_high": quote_row.get("time_high"),
                "time_low": quote_row.get("time_low"),
                "timestamp": quote.get("timestamp") or quote_row.get("time_close"),
                "open": float(quote["open"]),
                "high": float(quote["high"]),
                "low": float(quote["low"]),
                "close": close,
                "volume": float(quote["volume"]),
                "market_cap": market_cap,
                "circulating_supply": circulating_supply,
                "source": "coinmarketcap_api",
            }
        )
    return sorted(rows, key=lambda row: row["date"])


class CoinMarketCapClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = CMC_BASE_URL,
        timeout: float = 30.0,
        transport: CoinMarketCapTransport | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        max_attempts: int = 3,
        backoff_seconds: float = 2.0,
    ) -> None:
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.transport = transport or HttpxCoinMarketCapTransport()
        self.sleep = sleep
        self.max_attempts = max(1, max_attempts)
        self.backoff_seconds = max(0.0, backoff_seconds)

    async def fetch_bitcoin_ohlcv_historical(
        self,
        *,
        time_start: date,
        time_end: date,
        convert: str = "USD",
        bitcoin_id: int = 1,
    ) -> list[dict[str, Any]]:
        if not self.api_key:
            raise ValueError("COINMARKETCAP_API_KEY is required for remote refresh")

        headers = {"X-CMC_PRO_API_KEY": self.api_key}
        params = {
            "id": bitcoin_id,
            "time_start": time_start.isoformat(),
            "time_end": time_end.isoformat(),
            "time_period": "daily",
            "convert": convert,
        }
        last_error: CoinMarketCapTransientError | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                payload = await self.transport.get_json(
                    base_url=self.base_url,
                    timeout=self.timeout,
                    headers=headers,
                    params=params,
                )
                return cmc_ohlcv_payload_to_daily_rows(payload, convert=convert)
            except CoinMarketCapPermanentError:
                raise
            except CoinMarketCapTransientError as exc:
                last_error = exc
                if attempt >= self.max_attempts:
                    raise
                await self.sleep(self.backoff_seconds * (2 ** (attempt - 1)))

        if last_error is not None:
            raise last_error
        raise CoinMarketCapTransientError("CoinMarketCap request failed without a response")
