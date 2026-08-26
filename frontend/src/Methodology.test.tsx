import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { supportedLocales } from './locales'
import Methodology from './Methodology'
import { methodologyCopy, BAND_LOW, BAND_HIGH, METHODOLOGY_VERSION } from './methodologyCopy'

describe('methodology copy', () => {
  it('exists in every locale with the same section count', () => {
    const expected = methodologyCopy.en.sections.length
    expect(expected).toBeGreaterThanOrEqual(8)
    for (const locale of supportedLocales) {
      expect(methodologyCopy[locale].sections).toHaveLength(expected)
      for (const section of methodologyCopy[locale].sections) {
        expect(section.heading.trim().length).toBeGreaterThan(0)
        expect(section.body.length).toBeGreaterThan(0)
      }
    }
  })

  it('marks the six translations and leaves English unmarked', () => {
    expect(methodologyCopy.en.translationNotice).toBeNull()
    for (const locale of supportedLocales.filter((l) => l !== 'en')) {
      expect(methodologyCopy[locale].translationNotice).toBeTruthy()
    }
  })

  it('states the boundaries and version the backend uses', () => {
    expect(BAND_LOW).toBe(0.3)
    expect(BAND_HIGH).toBe(0.7)
    expect(METHODOLOGY_VERSION).toBe('crypto-scout-canonical-v1.1')
  })
})

describe('Methodology', () => {
  it('renders one h1 and one h2 per section', () => {
    render(<Methodology locale="en" />)
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
    expect(screen.getAllByRole('heading', { level: 2 })).toHaveLength(
      methodologyCopy.en.sections.length,
    )
  })

  it('shows the translation notice on a translated locale only', () => {
    const { unmount } = render(<Methodology locale="ru" />)
    expect(screen.getByText(methodologyCopy.ru.translationNotice!)).toBeTruthy()
    unmount()
    render(<Methodology locale="en" />)
    expect(screen.queryByText(/authoritative/i)).toBeNull()
  })

  it('links to the technical reference on the documentation site', () => {
    render(<Methodology locale="en" />)
    const link = screen.getByRole('link', { name: methodologyCopy.en.referenceLinkLabel })
    expect(link.getAttribute('href')).toBe(
      'https://docs.bitcoinriskbrief.minihub.app/product/risk-methodology/',
    )
  })

  it('renders no live risk value, because the guide explains rather than reports', () => {
    const { container } = render(<Methodology locale="en" />)
    expect(container.textContent).not.toMatch(/\brisk 0\.\d\d\b/i)
  })

  it('shows the risk boundaries and methodology version to the reader', () => {
    const { container } = render(<Methodology locale="en" />)
    expect(container.textContent).toContain('0.30')
    expect(container.textContent).toContain('0.70')
    expect(container.textContent).toContain('crypto-scout-canonical-v1.1')
  })
})
