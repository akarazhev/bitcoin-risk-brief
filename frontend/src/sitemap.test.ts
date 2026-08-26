import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { SITE_ORIGIN, siteDocuments } from './routes'

const xml = readFileSync(resolve(__dirname, '../public/sitemap.xml'), 'utf-8')
const listed = new Set([...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]))
const DOCS_URL = 'https://docs.bitcoinriskbrief.minihub.app/'

describe('sitemap', () => {
  it('lists every document', () => {
    for (const document of siteDocuments) {
      const expected = document.urlPath === '/' ? `${SITE_ORIGIN}/` : `${SITE_ORIGIN}${document.urlPath}`
      expect(listed).toContain(expected)
    }
  })

  it('lists nothing that is not a document, apart from the documentation site', () => {
    const allowed = new Set(
      siteDocuments.map((d) => (d.urlPath === '/' ? `${SITE_ORIGIN}/` : `${SITE_ORIGIN}${d.urlPath}`)),
    )
    allowed.add(DOCS_URL)
    for (const location of listed) {
      expect(allowed).toContain(location)
    }
  })
})
