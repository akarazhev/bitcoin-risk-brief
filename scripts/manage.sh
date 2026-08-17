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
    for migration in migrations/*.sql; do
      name="$(basename "${migration}")"
      ${COMPOSE} -f "${COMPOSE_FILE}" exec timescaledb \
        psql -U postgres -d bitcoin_risk_brief \
        -f "/docker-entrypoint-initdb.d/${name}"
    done
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
  warm-public-cache)
    ./scripts/warm-public-cache.sh
    ;;
  test-python)
    # Bare python3 is not the tests' interpreter. On Homebrew macOS it is now 3.14,
    # which cannot build pydantic-core or asyncpg (issues #21, #18), so every import
    # fails. Prefer the repository virtualenv; PYTHON overrides for CI, where
    # actions/setup-python already supplies a correct interpreter.
    PYTHON="${PYTHON:-}"
    if [[ -z "${PYTHON}" ]]; then
      if [[ -x .venv/bin/python ]]; then PYTHON=.venv/bin/python; else PYTHON=python3; fi
    fi
    if ! "${PYTHON}" -c 'import fastapi' >/dev/null 2>&1; then
      {
        echo "${PYTHON} cannot import fastapi, so the test dependencies are not installed for it."
        echo
        echo "Create the virtualenv the tests expect:"
        echo "  python3.13 -m venv .venv"
        echo "  .venv/bin/python -m pip install -r backend/requirements.txt -r collector/requirements.txt"
        echo
        echo "Python 3.14 will not work: pydantic-core and asyncpg have no wheels for it (issues #21, #18)."
      } >&2
      exit 1
    fi
    PYTHONPATH=backend:collector "${PYTHON}" -m unittest discover -s backend/tests -v
    PYTHONPATH=backend:collector "${PYTHON}" -m unittest discover -s collector/tests -v
    ;;
  help|*)
    echo "Usage: $0 {validate|migrate|start|stop|logs [service]|backfill|run-now|download-cmc-csv [expected-end-date]|import-cmc-csv <path> [expected-end-date]|warm-public-cache|test-python}"
    ;;
esac
