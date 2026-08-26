import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const distIndex = resolve(__dirname, '../dist/index.html')
const distMethodology = resolve(__dirname, '../dist/methodology.html')
const built = existsSync(distIndex) && existsSync(distMethodology)

function extractJsonLd(html: string): Record<string, unknown>[] {
  const matches = [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)]
  return matches.map((match) => JSON.parse(match[1]))
}

describe.skipIf(!built)('structured data (requires frontend/dist build)', () => {
  const indexHtml = readFileSync(distIndex, 'utf-8')
  const methodologyHtml = readFileSync(distMethodology, 'utf-8')

  it('is present and parses as JSON', () => {
    expect(extractJsonLd(indexHtml).length).toBeGreaterThan(0)
    expect(extractJsonLd(methodologyHtml).length).toBeGreaterThan(0)
  })

  it('declares Dataset and WebSite on home, and Dataset and TechArticle for the guide', () => {
    const homeTypes = extractJsonLd(indexHtml).map((entry) => entry['@type'])
    const guideTypes = extractJsonLd(methodologyHtml).map((entry) => entry['@type'])
    expect(homeTypes).toContain('Dataset')
    expect(homeTypes).toContain('WebSite')
    expect(guideTypes).toContain('Dataset')
    expect(guideTypes).toContain('TechArticle')
  })

  it('states the advice boundary on the dataset', () => {
    const dataset = extractJsonLd(indexHtml).find((entry) => entry['@type'] === 'Dataset')
    expect(String(dataset?.description).toLowerCase()).toContain('not financial advice')
  })

  it('does not license third-party BTC market data as Apache-2.0', () => {
    const dataset = extractJsonLd(indexHtml).find((entry) => entry['@type'] === 'Dataset')
    expect(dataset?.license).toBeUndefined()
    expect(String(dataset?.usageInfo).toLowerCase()).toContain('third-party btc/usd market data')
    expect(String(dataset?.usageInfo).toLowerCase()).toContain('not financial advice')
  })

  it('uses the canonical CSV start date for temporal coverage', () => {
    const dataset = extractJsonLd(indexHtml).find((entry) => entry['@type'] === 'Dataset')
    expect(dataset?.temporalCoverage).toBe('2010-07-13/..')
  })

  it('uses the generated document canonicals', () => {
    const guide = extractJsonLd(methodologyHtml).find((entry) => entry['@type'] === 'TechArticle')
    expect(guide?.url).toBe('https://bitcoinriskbrief.minihub.app/methodology')
  })

  it('embeds no concrete risk reading', () => {
    for (const html of [indexHtml, methodologyHtml]) {
      for (const entry of extractJsonLd(html)) {
        expect(JSON.stringify(entry)).not.toMatch(/\brisk\b[^"]*?\b0\.\d{3,}/i)
        expect(JSON.stringify(entry)).not.toMatch(/\\"risk\\"\s*:\s*0\.\d{3,}/i)
      }
    }
  })
})
