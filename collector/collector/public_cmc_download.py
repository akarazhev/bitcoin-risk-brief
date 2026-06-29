from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Protocol

from app.risk_sources import load_btc_usd_daily_csv, write_btc_usd_daily_csv
from collector.csv_refresh import last_completed_utc_day, validate_fetched_delta

CMC_PUBLIC_BASE_URL = "https://api.coinmarketcap.com"
CMC_PUBLIC_HISTORICAL_PATH = "/data-api/v3.1/cryptocurrency/historical"
CMC_PUBLIC_REFERER = "https://coinmarketcap.com/currencies/bitcoin/historical-data/"
CMC_USD_CONVERT_ID = "2781"


class PublicCoinMarketCapTransport(Protocol):
    async def get_json(
        self,
        *,
        base_url: str,
        path: str,
        timeout: float,
        headers: dict[str, str],
        params: dict[str, Any],
    ) -> dict[str, Any]:
        ...


class HttpxPublicCoinMarketCapTransport:
    async def get_json(
        self,
        *,
        base_url: str,
        path: str,
        timeout: float,
        headers: dict[str, str],
        params: dict[str, Any],
    ) -> dict[str, Any]:
        import httpx

        try:
            async with httpx.AsyncClient(base_url=base_url, timeout=timeout, follow_redirects=True) as client:
                response = await client.get(path, headers=headers, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            raise ValueError(f"CoinMarketCap public historical endpoint returned HTTP {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise ValueError(f"CoinMarketCap public historical endpoint request failed: {exc}") from exc
        except ValueError as exc:
            raise ValueError("CoinMarketCap public historical endpoint response JSON is invalid") from exc

        if not isinstance(payload, dict):
            raise ValueError("CoinMarketCap public historical endpoint response must be an object")
        return payload


@dataclass(frozen=True)
class PublicCoinMarketCapDownloadResult:
    downloaded_csv_path: Path
    row_count: int
    start_date: date
    end_date: date


def _unix_seconds(day: date, *, end_of_day: bool = False) -> int:
    clock = time(23, 59, 59) if end_of_day else time.min
    return int(datetime.combine(day, clock, tzinfo=timezone.utc).timestamp())


def _parse_utc_date(value: str) -> date:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def _parse_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, str):
        text = value.strip().replace(",", "")
        return float(text) if text else 0.0
    return float(value)


def _read_public_quote_value(quote: dict[str, Any], field_name: str) -> float:
    if field_name in quote:
        return _parse_float(quote[field_name])
    snake_case = ""
    for character in field_name:
        if character.isupper():
            snake_case += "_" + character.lower()
        else:
            snake_case += character
    return _parse_float(quote.get(snake_case))


def public_cmc_payload_to_daily_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    status = payload.get("status")
    if isinstance(status, dict):
        error_code = str(status.get("error_code", "0"))
        if error_code != "0":
            error_message = status.get("error_message") or "unknown error"
            raise ValueError(f"CoinMarketCap public historical endpoint returned error {error_code}: {error_message}")

    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("CoinMarketCap public historical endpoint response must contain a data object")
    quotes = data.get("quotes")
    if not isinstance(quotes, list):
        raise ValueError("CoinMarketCap public historical endpoint response must contain a quotes list")

    rows: list[dict[str, Any]] = []
    for quote_row in quotes:
        if not isinstance(quote_row, dict):
            raise ValueError("CoinMarketCap public historical endpoint quote row must be an object")
        quote = quote_row.get("quote")
        if not isinstance(quote, dict):
            raise ValueError("CoinMarketCap public historical endpoint quote row is missing quote data")

        time_open = quote_row.get("timeOpen") or quote_row.get("time_open")
        time_close = quote_row.get("timeClose") or quote_row.get("time_close")
        if not isinstance(time_open, str):
            raise ValueError("CoinMarketCap public historical endpoint quote row is missing timeOpen")

        close = _read_public_quote_value(quote, "close")
        market_cap = _read_public_quote_value(quote, "marketCap")
        circulating_supply = _read_public_quote_value(quote, "circulatingSupply")
        if circulating_supply <= 0 and close > 0:
            circulating_supply = market_cap / close

        rows.append(
            {
                "date": _parse_utc_date(time_open),
                "time_open": time_open,
                "time_close": time_close,
                "time_high": quote_row.get("timeHigh") or quote_row.get("time_high") or time_open,
                "time_low": quote_row.get("timeLow") or quote_row.get("time_low") or time_open,
                "timestamp": quote.get("timestamp") or time_close or time_open,
                "open": _read_public_quote_value(quote, "open"),
                "high": _read_public_quote_value(quote, "high"),
                "low": _read_public_quote_value(quote, "low"),
                "close": close,
                "volume": _read_public_quote_value(quote, "volume"),
                "market_cap": market_cap,
                "circulating_supply": circulating_supply,
                "source": "coinmarketcap_public",
            }
        )
    return sorted(rows, key=lambda row: row["date"])


class PublicCoinMarketCapClient:
    def __init__(
        self,
        *,
        base_url: str = CMC_PUBLIC_BASE_URL,
        bitcoin_id: int = 1,
        convert_id: str = CMC_USD_CONVERT_ID,
        timeout: float = 30.0,
        max_pages: int = 30,
        transport: PublicCoinMarketCapTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.bitcoin_id = bitcoin_id
        self.convert_id = convert_id
        self.timeout = timeout
        self.max_pages = max(1, max_pages)
        self.transport = transport or HttpxPublicCoinMarketCapTransport()

    async def _fetch_daily_window(self, *, start_date: date, end_date: date) -> list[dict[str, Any]]:
        payload = await self.transport.get_json(
            base_url=self.base_url,
            path=CMC_PUBLIC_HISTORICAL_PATH,
            timeout=self.timeout,
            headers={
                "Accept": "application/json,text/plain,*/*",
                "Origin": "https://coinmarketcap.com",
                "Referer": CMC_PUBLIC_REFERER,
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
                ),
            },
            params={
                "id": self.bitcoin_id,
                "convertId": self.convert_id,
                "timeStart": str(_unix_seconds(start_date)),
                "timeEnd": str(_unix_seconds(end_date, end_of_day=True)),
                "interval": "1d",
            },
        )
        return public_cmc_payload_to_daily_rows(payload)

    async def fetch_bitcoin_daily_rows(self, *, start_date: date, end_date: date) -> list[dict[str, Any]]:
        if start_date > end_date:
            return []

        rows_by_date: dict[date, dict[str, Any]] = {}
        cursor_end = end_date
        for _ in range(self.max_pages):
            window_rows = await self._fetch_daily_window(start_date=start_date, end_date=cursor_end)
            if not window_rows:
                break

            for row in window_rows:
                if start_date <= row["date"] <= end_date:
                    rows_by_date[row["date"]] = row

            expected_count = (end_date - start_date).days + 1
            if len(rows_by_date) >= expected_count:
                break

            earliest_date = window_rows[0]["date"]
            if earliest_date <= start_date:
                break

            next_cursor_end = earliest_date - timedelta(days=1)
            if next_cursor_end >= cursor_end:
                break
            cursor_end = next_cursor_end
        else:
            raise ValueError(
                "CoinMarketCap public historical endpoint did not cover requested range after "
                f"{self.max_pages} pages"
            )

        rows = [rows_by_date[day] for day in sorted(rows_by_date)]
        if not rows:
            raise ValueError(
                "CoinMarketCap public historical endpoint returned no BTC rows for "
                f"{start_date.isoformat()}..{end_date.isoformat()}"
            )
        validate_fetched_delta(rows, start_date=start_date, end_date=end_date)
        return rows


async def download_public_coinmarketcap_csv(
    canonical_csv_path: str | Path,
    incoming_dir: str | Path,
    *,
    expected_end_date: date | None = None,
    now: datetime | None = None,
    client: PublicCoinMarketCapClient | None = None,
) -> PublicCoinMarketCapDownloadResult | None:
    canonical_path = Path(canonical_csv_path)
    existing_rows = load_btc_usd_daily_csv(canonical_path)
    start_date = existing_rows[-1]["date"] + timedelta(days=1)
    end_date = expected_end_date or last_completed_utc_day(now)

    if start_date > end_date:
        return None

    downloader = client or PublicCoinMarketCapClient()
    fetched_rows = await downloader.fetch_bitcoin_daily_rows(start_date=start_date, end_date=end_date)

    output_dir = Path(incoming_dir)
    output_path = output_dir / f"coinmarketcap-public-btc-{start_date:%Y%m%d}-{end_date:%Y%m%d}.csv"
    write_btc_usd_daily_csv(output_path, fetched_rows)
    return PublicCoinMarketCapDownloadResult(
        downloaded_csv_path=output_path,
        row_count=len(fetched_rows),
        start_date=start_date,
        end_date=end_date,
    )
