import net from 'node:net'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { renderDocument } from './entry-server'
import { siteDocuments } from './routes'

const originalConnect = net.Socket.prototype.connect
const originalFetch = globalThis.fetch

beforeEach(() => {
  net.Socket.prototype.connect = function () {
    throw new Error('OUTBOUND NETWORK ATTEMPTED')
  } as never
  globalThis.fetch = (() => {
    throw new Error('OUTBOUND NETWORK ATTEMPTED')
  }) as unknown as typeof fetch
})

afterEach(() => {
  net.Socket.prototype.connect = originalConnect
  globalThis.fetch = originalFetch
})

describe('renderDocument', () => {
  it('renders every document without touching the network', () => {
    for (const document of siteDocuments) {
      const rendered = renderDocument(document.route, document.locale)
      expect(rendered.html.length).toBeGreaterThan(0)
      expect(rendered.head).toContain('rel="canonical"')
    }
  })

  it('carries the document language and direction', () => {
    expect(renderDocument('home', 'ar')).toMatchObject({ lang: 'ar', dir: 'rtl' })
    expect(renderDocument('methodology', 'de')).toMatchObject({ lang: 'de', dir: 'ltr' })
  })

  it('renders the guide text into the markup rather than leaving it to the client', () => {
    const { html } = renderDocument('methodology', 'ru')
    expect(html).toContain('<h1')
    expect(html.length).toBeGreaterThan(2000)
  })
})
