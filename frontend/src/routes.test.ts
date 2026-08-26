import { describe, expect, it } from 'vitest'
import { supportedLocales } from './locales'
import { documentForPath, siteDocuments, urlPathFor, SITE_ORIGIN } from './routes'

describe('site documents', () => {
  it('covers both routes in every locale and nothing else', () => {
    expect(siteDocuments).toHaveLength(supportedLocales.length * 2)
    for (const locale of supportedLocales) {
      expect(siteDocuments.some((d) => d.locale === locale && d.route === 'home')).toBe(true)
      expect(siteDocuments.some((d) => d.locale === locale && d.route === 'methodology')).toBe(true)
    }
  })

  it('gives English the unprefixed paths and every other locale a prefix', () => {
    expect(urlPathFor('home', 'en')).toBe('/')
    expect(urlPathFor('methodology', 'en')).toBe('/methodology')
    expect(urlPathFor('home', 'ru')).toBe('/ru')
    expect(urlPathFor('methodology', 'ru')).toBe('/ru/methodology')
    expect(urlPathFor('methodology', 'ar')).toBe('/ar/methodology')
  })

  it('never emits a trailing slash except at the root', () => {
    for (const document of siteDocuments) {
      if (document.urlPath === '/') continue
      expect(document.urlPath.endsWith('/')).toBe(false)
    }
  })

  it('maps each url path to a flat file, so nginx resolves it with $uri.html', () => {
    const byPath = Object.fromEntries(siteDocuments.map((d) => [d.urlPath, d.filePath]))
    expect(byPath['/']).toBe('index.html')
    expect(byPath['/ru']).toBe('ru.html')
    expect(byPath['/methodology']).toBe('methodology.html')
    expect(byPath['/ru/methodology']).toBe('ru/methodology.html')
  })

  it('resolves a pathname back to its document, and unknown paths to undefined', () => {
    expect(documentForPath('/ru/methodology')).toMatchObject({ route: 'methodology', locale: 'ru' })
    expect(documentForPath('/')).toMatchObject({ route: 'home', locale: 'en' })
    expect(documentForPath('/nonsense')).toBeUndefined()
    expect(documentForPath('/ru/')).toBeUndefined()
  })

  it('states the production origin without a trailing slash', () => {
    expect(SITE_ORIGIN).toBe('https://bitcoinriskbrief.minihub.app')
  })
})
