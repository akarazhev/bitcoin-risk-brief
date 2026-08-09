# OpenAPI

The machine-readable OpenAPI schema is served at:

```text
https://bitcoinriskbrief.minihub.app/api/openapi.json
```

It describes the seven public application endpoints: health, readiness, latest risk, risk history, risk levels, latest
brief, and waitlist submission. Generated code does not enforce the product's interpretation rules: clients must still
call `/api/readiness` first and must not present any output as financial advice, investment advice, a price forecast, or
a trading recommendation.

Interactive documentation is deliberately absent. The strict Content-Security-Policy blocks the CDN-loaded assets used
by the default Swagger UI, so the backend exposes the schema while leaving Swagger UI and ReDoc disabled. The CSP is not
relaxed for documentation.

## Generate a client

This example downloads the live schema with `curl`, then generates a Python client with
[OpenAPI Generator](https://openapi-generator.tech/docs/usage/):

```bash
curl --fail --silent --show-error \
  https://bitcoinriskbrief.minihub.app/api/openapi.json \
  --output bitcoin-risk-brief.openapi.json

openapi-generator-cli generate \
  --input-spec bitcoin-risk-brief.openapi.json \
  --generator-name python \
  --output generated/bitcoin-risk-brief-python
```

Review generated method names and models before integrating them, and put the readiness-first gate in the calling
workflow rather than assuming code generation adds it.
