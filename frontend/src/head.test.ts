import { describe, expect, it } from 'vitest'
import { supportedLocales } from './locales'
import { buildHead, renderHead } from './head'

describe('buildHead', () => {
  it('points canonical at its own document', () => {
    expect(buildHead('methodology', 'ru').canonical).toBe(
      'https://bitcoinriskbrief.minihub.app/ru/methodology',
    )
    expect(buildHead('home', 'en').canonical).toBe('https://bitcoinriskbrief.minihub.app/')
  })

  it('lists every locale plus x-default, which points at English', () => {
    const { alternates } = buildHead('methodology', 'de')
    expect(alternates).toHaveLength(supportedLocales.length + 1)
    const xDefault = alternates.find((a) => a.hreflang === 'x-default')
    expect(xDefault?.href).toBe('https://bitcoinriskbrief.minihub.app/methodology')
  })

  it('uses the full BCP-47 tag in hreflang, not the path segment', () => {
    const { alternates } = buildHead('home', 'en')
    expect(alternates.map((a) => a.hreflang)).toContain('zh-CN')
    expect(alternates.map((a) => a.hreflang)).not.toContain('zh')
  })

  it('carries the document language and direction', () => {
    expect(buildHead('home', 'ar')).toMatchObject({ lang: 'ar', dir: 'rtl' })
    expect(buildHead('home', 'de')).toMatchObject({ lang: 'de', dir: 'ltr' })
  })

  it('titles the guide differently from the home page in every locale', () => {
    for (const locale of supportedLocales) {
      expect(buildHead('methodology', locale).title).not.toBe(buildHead('home', locale).title)
      expect(buildHead('methodology', locale).title.length).toBeGreaterThan(0)
    }
  })
})

describe('renderHead', () => {
  it('emits every per-document social tag, and no static one', () => {
    const html = renderHead(buildHead('home', 'en'))
    for (const perDocument of ['og:title', 'og:description', 'og:url', 'twitter:title', 'twitter:description']) {
      expect(html).toContain(perDocument)
    }
    for (const static_ of ['og:image', 'og:site_name', 'og:type', 'twitter:card']) {
      expect(html).not.toContain(static_)
    }
  })

  it('emits one canonical link and one alternate per entry', () => {
    const html = renderHead(buildHead('methodology', 'ru'))
    expect(html.match(/rel="canonical"/g)).toHaveLength(1)
    expect(html.match(/rel="alternate"/g)).toHaveLength(supportedLocales.length + 1)
  })

  it('escapes quotes so an apostrophe in copy cannot break an attribute', () => {
    const html = renderHead({
      title: 'a "quoted" title',
      description: 'a "quoted" description',
      canonical: 'https://example.test/',
      lang: 'en',
      dir: 'ltr',
      alternates: [],
      jsonLd: '{}',
    })
    expect(html).not.toContain('content="a "quoted" description"')
    expect(html).toContain('&quot;')
  })
})
