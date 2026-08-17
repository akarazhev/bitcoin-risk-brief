import net from 'node:net'
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { ADVICE_LINE } from './format.js'
import { createServer } from './index.js'

function fakeFetch(impl: (url: string) => Response | Promise<Response>) {
  return vi.fn(async (input: string | URL) => impl(String(input))) as unknown as typeof fetch
}

function readinessResponse() {
  return new Response(JSON.stringify({
    status: 'ready',
    checks: {
      risk_data_available: true,
      validation_available: true,
      risk_range_ok: true,
      validation_has_rows: true,
      latest_matches_validation_end: true,
      source_is_canonical: true,
      data_fresh: true,
    },
    data: {
      covered_end: '2026-08-12',
      methodology_version: 'crypto-scout-canonical-v1.1',
    },
  }), { status: 200 })
}

function registeredTools(server: ReturnType<typeof createServer>) {
  return (server as unknown as { _registeredTools: Record<string, RegisteredTool> })._registeredTools
}

interface RegisteredTool {
  description?: string
  inputSchema: { parse(input: unknown): Record<string, unknown> }
  handler(args: Record<string, unknown>, context: unknown): Promise<{ content: Array<{ type: string; text: string }> }>
}

describe('MCP server wiring', () => {
  const originalConnect = net.Socket.prototype.connect

  beforeAll(() => {
    net.Socket.prototype.connect = function () {
      throw new Error('OUTBOUND NETWORK ATTEMPTED')
    } as never
  })

  afterAll(() => {
    net.Socket.prototype.connect = originalConnect
  })

  beforeEach(() => {
    process.env.BRB_API_BASE_URL = 'http://mcp-test.invalid'
  })

  afterEach(() => {
    delete process.env.BRB_API_BASE_URL
  })

  it('registers exactly the five read-only tools with the no-advice boundary', () => {
    const tools = registeredTools(createServer())

    expect(Object.keys(tools).sort()).toEqual([
      'check_readiness',
      'get_brief',
      'get_current_risk',
      'get_risk_history',
      'get_risk_levels',
    ])
    for (const tool of Object.values(tools)) {
      expect(tool.description).toContain('not financial advice')
    }
  })

  it('describes each tool distinctly, because a client picks a tool by its description', () => {
    const tools = registeredTools(createServer())
    const descriptions = Object.values(tools).map((tool) => tool.description ?? '')

    expect(new Set(descriptions).size).toBe(5)

    // Each description must name what the tool returns, or the model is choosing on the name alone.
    expect(tools.check_readiness.description).toContain('readiness')
    expect(tools.get_current_risk.description).toContain('latest')
    expect(tools.get_risk_history.description).toContain('90')
    expect(tools.get_risk_levels.description).toContain('ladder')
    expect(tools.get_brief.description).toContain('locale')
  })

  it('fetches readiness before the latest risk and includes the envelope', async () => {
    const seen: string[] = []
    const fetchImpl = fakeFetch((url) => {
      seen.push(url)
      if (url.endsWith('/api/readiness')) return readinessResponse()
      if (url.endsWith('/api/risk/latest')) {
        return new Response(JSON.stringify({ data: { risk: 0.23, risk_state: 'low' } }), { status: 200 })
      }
      throw new Error(`Unexpected URL: ${url}`)
    })
    const tools = registeredTools(createServer({ fetchImpl, now: new Date('2026-08-13T03:00:00Z') }))

    const result = await tools.get_current_risk.handler({}, {})

    expect(fetchImpl).toHaveBeenCalledTimes(2)
    expect(seen).toEqual([
      'http://mcp-test.invalid/api/readiness',
      'http://mcp-test.invalid/api/risk/latest',
    ])
    expect(result.content[0].text).toContain('data_state:')
  })

  it('renders a readiness 503 as an informative degraded state', async () => {
    const tools = registeredTools(createServer({
      fetchImpl: fakeFetch(() => new Response(JSON.stringify({
        status: 'degraded',
        checks: {
          risk_data_available: true,
          validation_available: true,
          risk_range_ok: true,
          validation_has_rows: true,
          latest_matches_validation_end: true,
          source_is_canonical: true,
          data_fresh: false,
        },
        data: {
          covered_end: '2026-08-09',
          methodology_version: 'crypto-scout-canonical-v1.1',
        },
      }), { status: 503 })),
      now: new Date('2026-08-13T03:00:00Z'),
    }))

    const result = await tools.check_readiness.handler({}, {})

    expect(result.content[0].text).toContain('Readiness status: degraded (HTTP 503).')
    expect(result.content[0].text).toContain('data_state:      stale')
    expect(result.content[0].text).toContain(ADVICE_LINE)
  })

  it('defaults risk history to 90 days and rejects days above 730', () => {
    const tools = registeredTools(createServer())

    expect(tools.get_risk_history.inputSchema.parse({})).toEqual({ days: 90 })
    expect(() => tools.get_risk_history.inputSchema.parse({ days: 731 })).toThrow()
  })

  it('requests a backend-valid history limit and renders one point when days is one', async () => {
    const seen: string[] = []
    const fetchImpl = fakeFetch((url) => {
      seen.push(url)
      if (url.endsWith('/api/readiness')) return readinessResponse()
      if (url.endsWith('/api/risk/history?limit=2')) {
        return new Response(JSON.stringify({
          data: [
            { timestamp: '2026-08-11T00:00:00Z', risk: 0.20, risk_state: 'low' },
            { timestamp: '2026-08-12T00:00:00Z', risk: 0.21, risk_state: 'low' },
          ],
        }), { status: 200 })
      }
      throw new Error(`Unexpected URL: ${url}`)
    })
    const tools = registeredTools(createServer({ fetchImpl, now: new Date('2026-08-13T03:00:00Z') }))

    const result = await tools.get_risk_history.handler({ days: 1 }, {})

    expect(seen).toEqual([
      'http://mcp-test.invalid/api/readiness',
      'http://mcp-test.invalid/api/risk/history?limit=2',
    ])
    expect(result.content[0].text).toContain('1 points returned.')
    expect(result.content[0].text).toContain('2026-08-12: risk 0.21 (low)')
    expect(result.content[0].text).not.toContain('2026-08-11: risk 0.20 (low)')
  })

  it('defaults the brief locale to English', async () => {
    const fetchImpl = fakeFetch((url) => {
      if (url.endsWith('/api/readiness')) return readinessResponse()
      if (url.endsWith('/api/brief/latest')) {
        return new Response(JSON.stringify({
          data: { sections: { en: { summary: 'English brief' } } },
        }), { status: 200 })
      }
      throw new Error(`Unexpected URL: ${url}`)
    })
    const tools = registeredTools(createServer({ fetchImpl, now: new Date('2026-08-13T03:00:00Z') }))
    const args = tools.get_brief.inputSchema.parse({})

    const result = await tools.get_brief.handler(args, {})

    expect(args).toEqual({ locale: 'en' })
    expect(result.content[0].text).toContain('Brief (en):')
    expect(result.content[0].text).toContain('English brief')
  })

  it('reports unreachable and malformed responses with the advice boundary once', async () => {
    const tools = registeredTools(createServer({
      fetchImpl: fakeFetch(() => {
        throw new TypeError('network down')
      }),
    }))

    const unreachable = await tools.get_current_risk.handler({}, {})

    expect(unreachable.content[0].text).toContain('API is unreachable')
    expect(unreachable.content[0].text).not.toMatch(/risk\s+\d/)
    expect(unreachable.content[0].text.split(ADVICE_LINE)).toHaveLength(2)

    const malformedTools = registeredTools(createServer({
      fetchImpl: fakeFetch(() => new Response('<html>502</html>', { status: 502 })),
    }))
    const malformed = await malformedTools.get_current_risk.handler({}, {})

    expect(malformed.content[0].text).toContain('malformed JSON')
    expect(malformed.content[0].text.split(ADVICE_LINE)).toHaveLength(2)
  })

  it('surfaces an upstream endpoint status instead of treating it as missing data', async () => {
    const tools = registeredTools(createServer({
      fetchImpl: fakeFetch((url) => {
        if (url.endsWith('/api/readiness')) return readinessResponse()
        if (url.endsWith('/api/risk/latest')) {
          return new Response(JSON.stringify({ detail: 'No current risk row is available.' }), { status: 500 })
        }
        throw new Error(`Unexpected URL: ${url}`)
      }),
    }))

    const result = await tools.get_current_risk.handler({}, {})

    expect(result.content[0].text).toContain('HTTP 500')
    expect(result.content[0].text).not.toContain('Response data is missing.')
  })

  it('uses fake fetch while every handler runs under the socket guard', async () => {
    const fetchImpl = fakeFetch((url) => {
      if (url.endsWith('/api/readiness')) return readinessResponse()
      if (url.endsWith('/api/risk/latest')) return new Response(JSON.stringify({ data: { risk: 0.23, risk_state: 'low' } }))
      if (url.endsWith('/api/risk/history?limit=2')) return new Response(JSON.stringify({ data: [] }))
      if (url.endsWith('/api/risk/levels')) return new Response(JSON.stringify({ data: [], meta: {} }))
      if (url.endsWith('/api/brief/latest')) return new Response(JSON.stringify({ data: { sections: { en: {} } } }))
      throw new Error(`Unexpected URL: ${url}`)
    })
    const tools = registeredTools(createServer({ fetchImpl, now: new Date('2026-08-13T03:00:00Z') }))

    await tools.check_readiness.handler({}, {})
    await tools.get_current_risk.handler({}, {})
    await tools.get_risk_history.handler({ days: 2 }, {})
    await tools.get_risk_levels.handler({}, {})
    await tools.get_brief.handler({ locale: 'en' }, {})

    expect(fetchImpl).toHaveBeenCalledTimes(9)
  })
})
