# Contributing

Thanks for looking at Bitcoin Risk Brief. This is a small, focused product, so the most useful contributions are
narrow ones.

## Before you start

Open an issue describing what you want to change and why. For anything touching risk methodology, database schema, or
the public API contract, agree on the approach in the issue first — those areas have compatibility and evidence rules
that are easy to break by accident.

## Running the stack

```bash
cp .env.example .env
./scripts/manage.sh validate
./scripts/manage.sh start
./scripts/manage.sh migrate
./scripts/manage.sh backfill
```

The product is then at `http://localhost:3001`.

## Checks

Run the checks that match what you changed:

| Change | Command |
| --- | --- |
| Backend or collector | `./scripts/manage.sh test-python` |
| Frontend behaviour | `npm test --prefix frontend` |
| Frontend build | `npm run build --prefix frontend` |
| Compose or operations | `./scripts/manage.sh validate` |
| Documentation | `mkdocs build --strict` |

## What we will not merge

- Changes that present the risk score as financial advice, a price forecast, or a trading signal.
- Anything that weakens the Content-Security-Policy or the no-tracking posture.
- New runtime dependencies without a stated reason.
- Claims in documentation that a reader cannot open and verify.

## Licence

Contributions are accepted under the Apache-2.0 licence in `LICENSE`.
