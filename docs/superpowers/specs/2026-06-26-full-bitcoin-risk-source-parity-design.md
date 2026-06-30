# Full Bitcoin Risk Source Parity Design

> Status: superseded. Last reviewed 2026-06-30. This was an intermediate CoinGecko/source-stitch design. Current
> implementation uses `collector/btc-csv/btc_usd_daily.csv` as the canonical source, public/manual CoinMarketCap CSV
> intake, and optional CoinMarketCap API delta refresh. Use `docs/data-pipeline.md` for current behavior.

**Goal:** give Bitcoin Risk Brief the same source-bootstrap discipline as `crypto-scout-analytics`: early local BTC CSV history, source stitch validation, and canonical risk calculation over the merged dataset.

## Scope

This change extends the existing `crypto-scout-canonical-v1` formula work with data-source parity:

- Copy the early BTC CoinMarketCap CSV files for 2010-2013 into the mini-product.
- Add a source module that loads and validates the CSV rows.
- Convert CoinGecko `market_chart` payloads into daily rows compatible with the canonical risk function.
- Merge early CSV rows and CoinGecko rows with daily gap checks.
- Validate the source stitch. If there is no overlap and no manual audit signoff, price features are accepted provisionally and turnover is disabled, matching `crypto-scout-analytics`.
- Persist CSV rows with `source='csv'` and CoinGecko rows with `source='coingecko'`.
- Store stitch diagnostics and canonical validation metadata in `btc_risk_validation.validation_json`.

## Runtime Behavior

`--backfill` becomes the canonical source-parity path. It loads CSV history, fetches CoinGecko history, validates the merge, calculates risk, and writes OHLCV/risk/validation/brief rows.

`--run-now` remains a rolling refresh path. It writes the latest CoinGecko rows, then recalculates risk over the locally persisted OHLCV history. If a canonical backfill has already been run, the refresh keeps the full context. If not, the refresh still works but has limited context.

## API Compatibility

No frontend API change is required. `/api/risk/latest`, `/api/risk/history`, `/api/risk/levels`, and `/api/brief/latest` keep their current response shapes.

## Limits

The mini-product still uses CoinGecko `market_chart`; it does not add the paid CoinGecko OHLC range endpoint in this pass. For historical rows where OHLC is not available from the mini collector, OHLC is close-only synthetic data. Full backfill still depends on CoinGecko returning enough later history for the configured plan.
