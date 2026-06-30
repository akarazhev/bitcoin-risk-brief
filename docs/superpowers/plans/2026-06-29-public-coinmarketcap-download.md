# Public CoinMarketCap Download Automation Plan

> Status: completed. Last reviewed 2026-06-30. Implemented by `collector/collector/public_cmc_download.py`,
> `collector.main --download-cmc-csv`, `./scripts/manage.sh download-cmc-csv [expected-end-date]`, and collector tests.

**Goal:** add an operator command that automatically fetches Bitcoin historical rows from CoinMarketCap's public historical-data JSON endpoint, stages a CSV, and reuses the existing validated CSV import path.

## Scope

- Add a downloader for `https://api.coinmarketcap.com/data-api/v3.1/cryptocurrency/historical`.
- Fetch the missing daily range after `collector/btc-csv/btc_usd_daily.csv` through an explicit expected end date, or the last completed UTC day by default.
- Filter CoinMarketCap's returned window down to the requested range and reject incomplete or non-contiguous responses.
- Write the fetched rows to `collector/btc-csv/incoming/`.
- Import that staged CSV through `import_coinmarketcap_downloaded_csv`.
- Add `collector.main --download-cmc-csv` and `./scripts/manage.sh download-cmc-csv [expected-end-date]`.
- Document that this public endpoint path is best-effort; manual CSV import and official API refresh remain supported.

## Verification

- Add focused collector unit tests for successful staging, no-op current data, endpoint failure, and non-contiguous responses.
- Run the collector test suite with `PYTHONPATH=backend:collector python3 -m unittest discover -s collector/tests -v`.
- Check CLI help and manage script usage include the new command.
