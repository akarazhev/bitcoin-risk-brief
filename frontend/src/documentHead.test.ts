import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const root = resolve(__dirname, '..')
const html = readFileSync(resolve(root, 'index.html'), 'utf-8')

describe('document head', () => {
  it('declares the svg icon, the png fallback and the apple touch icon', () => {
    expect(html).toContain('<link rel="icon" type="image/svg+xml" href="/favicon.svg"')
    expect(html).toContain('<link rel="icon" type="image/png" sizes="96x96" href="/favicon-96x96.png"')
    expect(html).toContain('<link rel="apple-touch-icon" href="/apple-touch-icon.png"')
  })

  it('every declared icon file exists in public/', () => {
    for (const name of ['favicon.svg', 'favicon-96x96.png', 'apple-touch-icon.png', 'og-image.png']) {
      expect(existsSync(resolve(root, 'public', name)), `public/${name} is missing`).toBe(true)
    }
  })

  it('declares an absolute og:image on the product host', () => {
    expect(html).toContain(
      '<meta property="og:image" content="https://bitcoinriskbrief.minihub.app/og-image.png"',
    )
    expect(html).toContain('<meta property="og:image:width" content="2560"')
    expect(html).toContain('<meta property="og:image:height" content="1280"')
    expect(html).toMatch(/<meta property="og:image:alt" content="[^"]{20,}"/)
  })

  it('upgrades the twitter card now that an image exists', () => {
    expect(html).toContain('<meta name="twitter:card" content="summary_large_image"')
    expect(html).not.toContain('content="summary"')
  })
})
