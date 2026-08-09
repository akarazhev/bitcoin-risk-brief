import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const html = readFileSync(resolve(__dirname, '../index.html'), 'utf-8')

function extractJsonLd(): Record<string, unknown>[] {
  const matches = [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)]
  return matches.map((match) => JSON.parse(match[1]))
}

describe('structured data', () => {
  it('is present and parses as JSON', () => {
    expect(extractJsonLd().length).toBeGreaterThan(0)
  })

  it('declares a Dataset and a WebSite', () => {
    const types = extractJsonLd().map((entry) => entry['@type'])
    expect(types).toContain('Dataset')
    expect(types).toContain('WebSite')
  })

  it('states the advice boundary on the dataset', () => {
    const dataset = extractJsonLd().find((entry) => entry['@type'] === 'Dataset')
    expect(String(dataset?.description).toLowerCase()).toContain('not financial advice')
  })

  it('embeds no concrete risk reading', () => {
    for (const entry of extractJsonLd()) {
      expect(JSON.stringify(entry)).not.toMatch(/\brisk\b[^"]*?\b0\.\d{3,}/i)
    }
  })
})
