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
