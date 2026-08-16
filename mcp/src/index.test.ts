import net from 'node:net'
import { describe, expect, it, vi } from 'vitest'
import { createServer } from './index.js'

function fakeFetch(impl: (url: string) => Response | Promise<Response>) {
  return vi.fn(async (input: string | URL) => impl(String(input))) as unknown as typeof fetch
}

function readinessResponse() {
  return new Response(JSON.stringify({
    status: 'ready',
    checks: { data_fresh: true },
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
      'https://bitcoinriskbrief.minihub.app/api/readiness',
      'https://bitcoinriskbrief.minihub.app/api/risk/latest',
    ])
    expect(result.content[0].text).toContain('data_state:')
  })

  it('defaults risk history to 90 days and rejects days above 730', () => {
    const tools = registeredTools(createServer())

    expect(tools.get_risk_history.inputSchema.parse({})).toEqual({ days: 90 })
    expect(() => tools.get_risk_history.inputSchema.parse({ days: 731 })).toThrow()
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

  it('reports an unreachable API without inventing a risk number', async () => {
    const tools = registeredTools(createServer({
      fetchImpl: fakeFetch(() => {
        throw new TypeError('network down')
      }),
    }))

    const result = await tools.get_current_risk.handler({}, {})

    expect(result.content[0].text).toContain('API is unreachable')
    expect(result.content[0].text).not.toMatch(/risk\s+\d/)
  })

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
})
