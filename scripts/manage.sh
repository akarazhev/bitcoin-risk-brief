#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-podman-compose.yml}"
COMPOSE="${COMPOSE:-podman-compose}"

case "${1:-help}" in
  validate)
    ${COMPOSE} -f "${COMPOSE_FILE}" config >/dev/null
    echo "compose config ok"
    ;;
  migrate)
    ${COMPOSE} -f "${COMPOSE_FILE}" exec timescaledb psql -U postgres -d bitcoin_risk_brief -f /docker-entrypoint-initdb.d/001_initial_schema.sql
    ;;
  start)
    ${COMPOSE} -f "${COMPOSE_FILE}" up -d --build
    ;;
  stop)
    ${COMPOSE} -f "${COMPOSE_FILE}" down
    ;;
  logs)
    ${COMPOSE} -f "${COMPOSE_FILE}" logs -f "${2:-}"
    ;;
  backfill)
    ${COMPOSE} -f "${COMPOSE_FILE}" run --rm data-collector python -m collector.main --backfill
    ;;
  run-now)
    ${COMPOSE} -f "${COMPOSE_FILE}" run --rm data-collector python -m collector.main --run-now
    ;;
  download-cmc-csv)
    extra_args=()
    if [[ -n "${2:-}" ]]; then
      extra_args=(--expected-end-date "${2}")
    fi
    ${COMPOSE} -f "${COMPOSE_FILE}" run --rm data-collector \
      python -m collector.main --download-cmc-csv "${extra_args[@]}"
    ;;
  import-cmc-csv)
    if [[ -z "${2:-}" ]]; then
      echo "Usage: $0 import-cmc-csv collector/btc-csv/incoming/bitcoin-historical-data.csv [expected-end-date]" >&2
      exit 2
    fi
    input_path="${2#./}"
    if [[ "${input_path}" != collector/btc-csv/incoming/* ]]; then
      echo "Stage downloaded CSV under collector/btc-csv/incoming/ so the data-collector container can read it" >&2
      exit 2
    fi
    extra_args=()
    if [[ -n "${3:-}" ]]; then
      extra_args=(--expected-end-date "${3}")
    fi
    ${COMPOSE} -f "${COMPOSE_FILE}" run --rm data-collector \
      python -m collector.main --import-cmc-csv "/app/${input_path}" "${extra_args[@]}"
    ;;
  test-python)
    PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -v
    PYTHONPATH=backend:collector python3 -m unittest discover -s collector/tests -v
    ;;
  help|*)
    echo "Usage: $0 {validate|migrate|start|stop|logs [service]|backfill|run-now|download-cmc-csv [expected-end-date]|import-cmc-csv <path> [expected-end-date]|test-python}"
    ;;
esac
