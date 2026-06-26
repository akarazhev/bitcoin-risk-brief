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
  test-python)
    PYTHONPATH=backend:collector python3 -m unittest discover -s backend/tests -v
    PYTHONPATH=backend:collector python3 -m unittest discover -s collector/tests -v
    ;;
  help|*)
    echo "Usage: $0 {validate|migrate|start|stop|logs [service]|backfill|run-now|test-python}"
    ;;
esac
