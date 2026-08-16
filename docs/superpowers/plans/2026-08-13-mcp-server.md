# MCP Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship an MCP server that lets any client read the Bitcoin risk signal correctly, installable with one `npx` line.

**Architecture:** A TypeScript package in `mcp/`, four focused source files: an HTTP client over the existing public API, a pure module deriving the freshness envelope, pure response formatters, and the server wiring. No backend change, no new endpoint, no computation of risk.

**Tech Stack:** TypeScript, `@modelcontextprotocol/server` (SDK v2), Zod v4, Vitest, Node 22.

Design: [MCP Server Design](../specs/2026-08-13-mcp-server-design.md).

## Global Constraints

- **The server is read-only.** No tool writes anything. The interest form is not exposed.
- **No network in tests, ever.** Every test injects a fake fetch. One test asserts that no socket opens.
- **No risk computation.** The server reads the public API and calculates nothing beyond `data_state`.
- **No change to product behaviour.** Specifically: nothing under `backend/app/`, `collector/collector/`, or
  `frontend/src/`, and no change to the database or the methodology.
  Task 6 does touch two files that sit under those trees but are not product code — `frontend/public/llms.txt` is a
  static agent file, and `backend/tests/test_agent_surface.py` is where every assertion about the agent surface already
  lives. Both are in scope for that task; a parallel test file would fragment the surface's coverage.
- Base URL comes from `BRB_API_BASE_URL`, defaulting to `https://bitcoinriskbrief.minihub.app`.
- **Every data response carries the freshness envelope.** This is the acceptance criterion and it is structural, not advisory.
- Every tool description states the analytics-not-advice boundary, and every response repeats it once.
- SDK v2 package names: `@modelcontextprotocol/server` and `@modelcontextprotocol/server/stdio`. The monolithic `@modelcontextprotocol/sdk` is retired — do not use it.
- Zod v4 is imported as `import * as z from 'zod/v4'`. A tool without parameters declares `inputSchema: z.object({})`.

## File Structure

| File | Responsibility |
| --- | --- |
| `mcp/package.json` | Package metadata, bin entry, scripts |
| `mcp/tsconfig.json` | Compiler settings |
| `mcp/src/api.ts` | HTTP calls to the public API and the error taxonomy. The only file that knows about `fetch`. |
| `mcp/src/freshness.ts` | Derives `data_state` and renders the envelope. Pure. |
| `mcp/src/format.ts` | Turns API payloads into tool response text, including the degraded shape. Pure. |
| `mcp/src/index.ts` | Creates the server, registers five tools, serves stdio. Wiring only. |
| `mcp/README.md` | Install line and a worked readiness-first example |

`api.ts` is the only module that performs I/O. Everything else is pure and testable without a transport, which is what makes the envelope rules cheap to cover.

---

### Task 1: Package scaffold and CI

**Files:**
- Create: `mcp/package.json`, `mcp/tsconfig.json`, `mcp/src/version.ts`, `mcp/src/version.test.ts`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Produces: `SERVER_NAME` and `SERVER_VERSION` exported from `mcp/src/version.ts`, used by Task 5 when constructing `McpServer`.

- [ ] **Step 1: Write the failing test**

Create `mcp/src/version.test.ts`:

```typescript
import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { SERVER_NAME, SERVER_VERSION } from './version.js'

describe('package identity', () => {
  it('matches package.json so the server never reports a version it is not', () => {
    const pkg = JSON.parse(readFileSync(resolve(__dirname, '../package.json'), 'utf-8'))
    expect(SERVER_VERSION).toBe(pkg.version)
    expect(SERVER_NAME).toBe('bitcoin-risk-brief')
  })
})
```

The test exists because a hardcoded version that drifts from `package.json` makes a client report the wrong server build, and nothing else would catch it.

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test --prefix mcp`
Expected: FAIL — no package, no module.

- [ ] **Step 3: Create the package**

`mcp/package.json`:

```json
{
  "name": "@akarazhev/bitcoin-risk-brief-mcp",
  "version": "0.1.0",
  "description": "MCP server for the Bitcoin Risk Brief public API. Analytics and research context, not financial advice.",
  "license": "Apache-2.0",
  "type": "module",
  "bin": { "bitcoin-risk-brief-mcp": "dist/index.js" },
  "files": ["dist"],
  "engines": { "node": ">=22" },
  "scripts": {
    "build": "tsc -b",
    "test": "vitest run",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@modelcontextprotocol/server": "^2.0.0",
    "zod": "^4.0.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "typescript": "^5.6.0",
    "vitest": "^2.0.0"
  }
}
```

Pin the dependency versions to whatever `npm install` actually resolves, and report those versions. Do not leave a range that was never installed.

`mcp/tsconfig.json` targets `ES2022`, `module: NodeNext`, `outDir: dist`, `strict: true`, and includes `src`.

`mcp/src/version.ts`:

```typescript
export const SERVER_NAME = 'bitcoin-risk-brief'
export const SERVER_VERSION = '0.1.0'
```

- [ ] **Step 4: Add the CI job**

Append to `.github/workflows/ci.yml`:

```yaml
  mcp-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: npm
          cache-dependency-path: mcp/package-lock.json
      - name: Install MCP server dependencies
        run: npm ci --prefix mcp
      - name: Type-check
        run: npm run typecheck --prefix mcp
      - name: Test
        run: npm test --prefix mcp
      - name: Build
        run: npm run build --prefix mcp
```

- [ ] **Step 5: Run the checks and commit**

Run: `npm install --prefix mcp && npm test --prefix mcp`
Expected: PASS.

```bash
git add mcp .github/workflows/ci.yml
git commit -m "build: scaffold the MCP server package"
```

---

### Task 2: API client

**Files:**
- Create: `mcp/src/api.ts`, `mcp/src/api.test.ts`

**Interfaces:**
- Produces:
  - `type Fetch = typeof fetch`
  - `class ApiUnreachable extends Error` — the request never completed
  - `class ApiMalformed extends Error` — a response arrived that is not usable JSON
  - `async function getJson(path: string, opts?: { fetchImpl?: Fetch }): Promise<{ status: number; body: unknown }>`
  - `function baseUrl(): string`

- [ ] **Step 1: Write the failing test**

Create `mcp/src/api.test.ts`:

```typescript
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiMalformed, ApiUnreachable, baseUrl, getJson } from './api.js'

function fakeFetch(impl: (url: string) => Response | Promise<Response>) {
  return vi.fn(async (input: string | URL) => impl(String(input))) as unknown as typeof fetch
}

afterEach(() => {
  delete process.env.BRB_API_BASE_URL
})

describe('baseUrl', () => {
  it('defaults to production', () => {
    expect(baseUrl()).toBe('https://bitcoinriskbrief.minihub.app')
  })

  it('honours the environment override so tests never reach production', () => {
    process.env.BRB_API_BASE_URL = 'http://localhost:9999'
    expect(baseUrl()).toBe('http://localhost:9999')
  })

  it('strips a trailing slash so paths do not double up', () => {
    process.env.BRB_API_BASE_URL = 'http://localhost:9999/'
    expect(baseUrl()).toBe('http://localhost:9999')
  })
})

describe('getJson', () => {
  it('returns the status alongside the body, so a 503 is information rather than a failure', async () => {
    const fetchImpl = fakeFetch(() => new Response(JSON.stringify({ status: 'degraded' }), { status: 503 }))
    const result = await getJson('/api/readiness', { fetchImpl })

    expect(result.status).toBe(503)
    expect(result.body).toEqual({ status: 'degraded' })
  })

  it('reports an unreachable API distinctly from a bad response', async () => {
    const fetchImpl = fakeFetch(() => {
      throw new TypeError('network down')
    })
    await expect(getJson('/api/readiness', { fetchImpl })).rejects.toBeInstanceOf(ApiUnreachable)
  })

  it('reports a non-JSON body as malformed', async () => {
    const fetchImpl = fakeFetch(() => new Response('<html>502</html>', { status: 502 }))
    await expect(getJson('/api/readiness', { fetchImpl })).rejects.toBeInstanceOf(ApiMalformed)
  })

  it('requests the path against the configured base', async () => {
    process.env.BRB_API_BASE_URL = 'http://localhost:9999'
    const seen: string[] = []
    const fetchImpl = fakeFetch((url) => {
      seen.push(url)
      return new Response('{}', { status: 200 })
    })
    await getJson('/api/risk/latest', { fetchImpl })

    expect(seen).toEqual(['http://localhost:9999/api/risk/latest'])
  })
})
```

Three failure modes are three classes on purpose. A model that cannot reach the API must say so rather than invent a value, and "unreachable" and "returned nonsense" are different things to tell it.

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test --prefix mcp`
Expected: FAIL — `./api.js` does not exist.

- [ ] **Step 3: Write the client**

`getJson` reads `baseUrl()`, joins the path, calls `fetchImpl ?? globalThis.fetch`, wraps any thrown error in `ApiUnreachable`, parses the body and wraps a parse failure in `ApiMalformed`, and returns `{ status, body }` without throwing on non-2xx. A timeout of 15 seconds is applied with `AbortSignal.timeout(15_000)`.

- [ ] **Step 4: Run tests**

Run: `npm test --prefix mcp`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add mcp/src/api.ts mcp/src/api.test.ts
git commit -m "feat: add the public API client"
```

---

### Task 3: The freshness envelope

**Files:**
- Create: `mcp/src/freshness.ts`, `mcp/src/freshness.test.ts`

**Interfaces:**
- Produces:
  - `type DataState = 'current' | 'behind' | 'stale'`
  - `interface Envelope`, defined below
  - `function lastCompletedUtcDay(now?: Date): string` returning `YYYY-MM-DD`
  - `function deriveEnvelope(readiness: unknown, now?: Date): Envelope`
  - `function renderEnvelope(envelope: Envelope): string`

```typescript
export interface Envelope {
  coveredThrough: string | null
  dataState: DataState
  methodology: string | null
  // Readiness diagnostics. Not rendered by renderEnvelope — consumed by the stale banner in Task 4.
  dataFresh: boolean | null
  dataAgeDays: number | null
  maxAgeDays: number | null
}
```

This is the module the acceptance criterion rests on, and it is pure — no network, no SDK, no I/O.

- [ ] **Step 1: Write the failing test**

Create `mcp/src/freshness.test.ts`:

```typescript
import { describe, expect, it } from 'vitest'
import { deriveEnvelope, lastCompletedUtcDay, renderEnvelope } from './freshness.js'

const NOW = new Date('2026-08-13T03:00:00Z')

function readiness(
  status: string,
  coveredEnd: string | null,
  { dataFresh = true, ageDays = 1, maxAgeDays = 2 } = {},
) {
  return {
    status,
    checks: { data_fresh: dataFresh },
    data: {
      covered_end: coveredEnd,
      data_age_days: ageDays,
      max_age_days: maxAgeDays,
      methodology_version: 'crypto-scout-canonical-v1.1',
    },
  }
}

describe('lastCompletedUtcDay', () => {
  it('is yesterday in UTC', () => {
    expect(lastCompletedUtcDay(NOW)).toBe('2026-08-12')
  })

  it('crosses a month boundary correctly', () => {
    expect(lastCompletedUtcDay(new Date('2026-09-01T00:30:00Z'))).toBe('2026-08-31')
  })
})

describe('deriveEnvelope', () => {
  it('is current when the observation covers the last completed day', () => {
    expect(deriveEnvelope(readiness('ready', '2026-08-12'), NOW).dataState).toBe('current')
  })

  it('is behind when readiness is ready but the day is older', () => {
    expect(deriveEnvelope(readiness('ready', '2026-08-11'), NOW).dataState).toBe('behind')
  })

  it('is stale whenever readiness is not ready, however recent the date', () => {
    expect(deriveEnvelope(readiness('degraded', '2026-08-12'), NOW).dataState).toBe('stale')
  })

  it('is stale when readiness cannot be understood at all', () => {
    expect(deriveEnvelope(null, NOW).dataState).toBe('stale')
    expect(deriveEnvelope({ nonsense: true }, NOW).dataState).toBe('stale')
  })

  it('carries the covered date and the methodology through', () => {
    const envelope = deriveEnvelope(readiness('ready', '2026-08-12'), NOW)
    expect(envelope.coveredThrough).toBe('2026-08-12')
    expect(envelope.methodology).toBe('crypto-scout-canonical-v1.1')
  })

  it('carries the readiness diagnostics the stale banner needs', () => {
    const envelope = deriveEnvelope(
      readiness('degraded', '2026-08-09', { dataFresh: false, ageDays: 3, maxAgeDays: 2 }),
      NOW,
    )
    expect(envelope.dataFresh).toBe(false)
    expect(envelope.dataAgeDays).toBe(3)
    expect(envelope.maxAgeDays).toBe(2)
  })

  it('leaves the diagnostics null when readiness cannot be understood', () => {
    const envelope = deriveEnvelope(null, NOW)
    expect(envelope.dataFresh).toBeNull()
    expect(envelope.dataAgeDays).toBeNull()
    expect(envelope.maxAgeDays).toBeNull()
  })
})

describe('renderEnvelope', () => {
  it('names all three fields so a model cannot receive a value without them', () => {
    const text = renderEnvelope(deriveEnvelope(readiness('ready', '2026-08-12'), NOW))
    expect(text).toContain('covered_through: 2026-08-12')
    expect(text).toContain('data_state:      current')
    expect(text).toContain('methodology:     crypto-scout-canonical-v1.1')
  })

  it('prints exactly three lines — diagnostics belong to the stale banner, not the envelope', () => {
    const text = renderEnvelope(deriveEnvelope(readiness('ready', '2026-08-12'), NOW))
    expect(text.split('\n')).toHaveLength(3)
  })
})
```

`deriveEnvelope(null)` returning `stale` matters: an unreadable readiness response is not a reason to present data as fresh.

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test --prefix mcp`
Expected: FAIL — `./freshness.js` does not exist.

- [ ] **Step 3: Write the module**

`lastCompletedUtcDay` subtracts one day using `Date.UTC` arithmetic — never by decrementing the day number, which breaks at month and year boundaries.

`deriveEnvelope` returns `stale` unless the readiness payload is an object whose `status` is exactly `'ready'`; then `current` if `covered_end` equals `lastCompletedUtcDay(now)`, otherwise `behind`.

`deriveEnvelope` also lifts three readiness diagnostics: `dataFresh` from `checks.data_fresh`, `dataAgeDays` from
`data.data_age_days`, and `maxAgeDays` from `data.max_age_days`. Each is `null` when absent or the wrong type. These
exist because Task 4's stale banner must state how stale, and `deriveEnvelope` is the only place that parses the
readiness payload — parsing it a second time in `format.ts` would let two answers to "is this current" drift apart.

Note that `data_age_days` is computed by the backend from `latest_date`, not from `covered_end`. In a healthy system
they are equal, which is what the `latest_matches_validation_end` check asserts; in a degraded one they may differ.
Report each as what it is and do not derive one from the other.

`renderEnvelope` pads the labels so the three lines align, and prints `unknown` for a null field rather than omitting
the line. It renders **only** `covered_through`, `data_state` and `methodology` — the diagnostics are deliberately not
in it, because the three-line envelope is the design's structural contract for every response.

- [ ] **Step 4: Run tests**

Run: `npm test --prefix mcp`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add mcp/src/freshness.ts mcp/src/freshness.test.ts
git commit -m "feat: derive and render the freshness envelope"
```

---

### Task 4: Response formatters

**Files:**
- Create: `mcp/src/format.ts`, `mcp/src/format.test.ts`

**Interfaces:**
- Consumes: `Envelope`, `renderEnvelope` from Task 3.
- Produces:
  - `formatReadiness`, `formatCurrentRisk`, `formatHistory`, `formatLevels` — each `(payload: unknown, envelope: Envelope) => string`
  - `formatBrief(payload: unknown, envelope: Envelope, locale: string) => string`
  - `const ADVICE_LINE: string`

`formatBrief` is the one formatter that takes a third argument, because it is the one whose payload does not carry the
answer: `/api/brief/latest` returns every locale in `data.sections` and the tool was asked for exactly one. A uniform
signature here would be uniformity bought by making the formatter guess.

- [ ] **Step 1: Write the failing test**

Create `mcp/src/format.test.ts` covering, one test each:

1. `formatCurrentRisk` includes the risk value, the state, and the rendered envelope.
2. `formatCurrentRisk` with a `stale` envelope **begins** with `DATA IS STALE — do not present these values as current.`, still contains the last known risk value, and carries `Readiness reports: data_fresh false, 3 days old, tolerance 2 days.` built from the envelope's diagnostics.
3. `formatCurrentRisk` with a `behind` envelope names the covered date without the stale banner.
4. Every formatter's output ends with `ADVICE_LINE`.
5. `ADVICE_LINE` contains `not financial advice`.
6. `formatHistory` renders one line per point and states how many were returned.
7. `formatBrief(payload, envelope, 'ru')` renders the `ru` section and nothing from the other six — assert a phrase unique to each other section is absent.
8. `formatLevels` renders the ladder and the evaluation date.
9. A payload missing its `data` key produces a message saying so rather than throwing.
10. A `stale` envelope whose diagnostics are all `null` omits the `Readiness reports:` line entirely rather than
    printing `null` or `undefined` into it.
11. `formatBrief` asked for a locale the snapshot does not carry says so and names the locales it does carry, rather
    than silently rendering `en`.

Use payload fixtures copied from `docs/engineering/api-reference.md`, not invented shapes.

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test --prefix mcp`
Expected: FAIL — `./format.js` does not exist.

- [ ] **Step 3: Write the formatters**

Each formatter renders the envelope first when `dataState` is `stale`, and after the values otherwise. The stale form:

```text
DATA IS STALE — do not present these values as current.
Last known observation: risk 0.23 (low), covered through 2026-08-09.
Readiness reports: data_fresh false, 3 days old, tolerance 2 days.
```

The third line is built entirely from `Envelope`: `dataFresh`, `dataAgeDays`, `maxAgeDays`. The formatters never see
the raw readiness payload and never parse it. When all three are `null` — readiness was unreadable — omit that line.
This is the rule the product already applies to `low_usd` and `high_usd`: hide a value rather than show a wrong one.
The first two lines stay regardless, because "the data is stale and I cannot tell you how stale" is still the honest
answer and still forbids presenting the values as current.

`formatBrief` selects `data.sections[locale]`. The API documents that older persisted snapshots may carry only `en`
and `ru`, so a requested locale can legitimately be absent. When it is, say which locales the snapshot does carry and
render no section at all. Do not fall back to `en`: handing a model English prose it did not ask for, without saying
so, is the silent substitution this product exists to avoid — and the model can re-ask for a locale it now knows
exists. The envelope and `ADVICE_LINE` still appear in that response.

`ADVICE_LINE` is a single sentence appended to every response: analytics and research context, not financial advice, not a price forecast, and not a trade signal.

Numbers are formatted for reading: risk to two decimals, prices with thousands separators and no decimals.

- [ ] **Step 4: Run tests**

Run: `npm test --prefix mcp`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add mcp/src/format.ts mcp/src/format.test.ts
git commit -m "feat: format tool responses with the envelope"
```

---

### Task 5: Register the tools and serve

**Files:**
- Create: `mcp/src/index.ts`, `mcp/src/index.test.ts`
- Create: `mcp/README.md`

**Interfaces:**
- Consumes: everything from Tasks 1-4.
- Produces: `function createServer(deps?: { fetchImpl?: Fetch; now?: Date }): McpServer`, exported so tests can build a server without a transport.

- [ ] **Step 1: Write the failing test**

Create `mcp/src/index.test.ts`. Build the server with `createServer({ fetchImpl })` and assert:

1. exactly five tools are registered, named `check_readiness`, `get_current_risk`, `get_risk_history`, `get_risk_levels`, `get_brief`;
2. every tool description contains `not financial advice`;
3. calling `get_current_risk` fetches readiness **and** the latest risk, and the result contains `data_state:`;
4. `get_risk_history` defaults to 90 days and rejects a `days` above 730;
5. `get_brief` defaults to locale `en`;
6. when the fake fetch throws, the result says the API is unreachable and contains no risk number.

Then a socket guard, which is the constraint made executable:

```typescript
import net from 'node:net'

it('opens no socket during the whole suite', async () => {
  const original = net.Socket.prototype.connect
  net.Socket.prototype.connect = function () {
    throw new Error('OUTBOUND NETWORK ATTEMPTED')
  } as never
  try {
    const server = createServer({ fetchImpl: fakeFetch(() => new Response('{}', { status: 200 })) })
    expect(server).toBeDefined()
  } finally {
    net.Socket.prototype.connect = original
  }
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test --prefix mcp`
Expected: FAIL — `./index.js` does not exist.

- [ ] **Step 3: Write the wiring**

```typescript
import { McpServer } from '@modelcontextprotocol/server'
import { serveStdio } from '@modelcontextprotocol/server/stdio'
import * as z from 'zod/v4'
import { SERVER_NAME, SERVER_VERSION } from './version.js'
```

`createServer` builds `new McpServer({ name: SERVER_NAME, version: SERVER_VERSION })` and calls `registerTool` five times. Tools without parameters declare `inputSchema: z.object({})`. `get_risk_history` declares `z.object({ days: z.number().int().min(1).max(730).default(90) })`; `get_brief` declares `z.object({ locale: z.enum(['en','ru','zh','de','fr','es','ar']).default('en') })`.

Every handler fetches `/api/readiness` first, derives the envelope, then fetches its own endpoint — so no handler can return data without the envelope even if a future edit forgets.

The `get_brief` handler passes its validated `locale` straight through to `formatBrief`. `index.ts` never inspects or
filters `data.sections` itself: payload shape is `format.ts`'s responsibility, and splitting it across both modules
would put the missing-locale case in the one module that has no test for payload shapes.

Handlers return `{ content: [{ type: 'text', text }] }`.

The module ends with `serveStdio(() => createServer())` guarded so importing the file in a test does not start a transport.

Write `mcp/README.md` with the one-line install, the five tools, and a worked example of the readiness-first sequence.

- [ ] **Step 4: Run the checks**

Run: `npm test --prefix mcp && npm run typecheck --prefix mcp && npm run build --prefix mcp`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add mcp/src/index.ts mcp/src/index.test.ts mcp/README.md
git commit -m "feat: register the five tools and serve over stdio"
```

---

### Task 6: Documentation

**Files:**
- Create: `docs/agents/mcp-server.md`
- Modify: `mkdocs.yml`, `frontend/public/llms.txt`, `docs/llms.txt`, `docs/agents/index.md`
- Test: `backend/tests/test_agent_surface.py`

**Interfaces:**
- Consumes: the package name from Task 1.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_agent_surface.py` a test asserting `docs/agents/mcp-server.md` exists, names the install command, and states the no-advice boundary; and that `frontend/public/llms.txt` links the MCP page so an agent arriving by crawl finds the installable path.

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=backend:collector python -m unittest discover -s backend/tests -k agent_surface -v`
Expected: FAIL.

- [ ] **Step 3: Write the page and the links**

`docs/agents/mcp-server.md` covers the install line, the five tools with their parameters, the freshness envelope and why it is always present, the degraded shape, and the no-advice boundary. Add it to `mkdocs.yml` under `Agents`, link it from `docs/agents/index.md`, and add one line to both `llms.txt` files pointing at it.

Remember the constraint the existing test enforces: `docs/llms.txt` entries put the description first and the URL last, with nothing after it.

- [ ] **Step 4: Run the checks**

Run: `PYTHONPATH=backend:collector python -m unittest discover -s backend/tests`
Run: `mkdocs build --strict`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs mkdocs.yml frontend/public/llms.txt backend/tests/test_agent_surface.py
git commit -m "docs: document the MCP server"
```

---

### Task 7: Publish

Operator work, performed after the branch merges and `mcp-build` reports green on `main`. Not test-driven.

- [ ] **Step 1: Confirm the job ran green on `main`**

- [ ] **Step 2: Publish to npm**

```bash
npm publish --prefix mcp --access public
```

- [ ] **Step 3: Verify the install path a user would take**

```bash
npx -y @akarazhev/bitcoin-risk-brief-mcp
```

Expected: the process starts and waits on stdin. It is an MCP server; a bare run producing no output is correct.

- [ ] **Step 4: Submit to the official MCP Registry**

- [ ] **Step 5: Add `mcp-build` to the required checks**

Read the `main` ruleset, append `{ "context": "mcp-build" }` to `required_status_checks`, and write it back without disturbing the `deletion`, `non_fast_forward` and `pull_request` rules.

---

## Verification Summary

```bash
npm test --prefix mcp
npm run typecheck --prefix mcp
npm run build --prefix mcp
./scripts/manage.sh test-python
npm test --prefix frontend
npm run build --prefix frontend
./scripts/manage.sh validate
mkdocs build --strict
```

## Out Of Scope

- Any write operation, authentication, quota, or key.
- A hosted or remote server; stdio only.
- Computing risk in the server.
- A Python implementation.
- Changes to product behaviour: `backend/app/`, `collector/collector/`, `frontend/src/`, the database, or the methodology.
