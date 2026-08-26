import { render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { LOCALE_STORAGE_KEY } from './localePreference'
import { Root } from './Root'

const replace = vi.fn()

beforeEach(() => {
  localStorage.clear()
  replace.mockClear()
  vi.stubGlobal('location', { pathname: '/', replace } as unknown as Location)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('Root', () => {
  it('renders the guide when the route says so', () => {
    render(<Root route="methodology" locale="en" />)
    expect(screen.getByRole('heading', { level: 1 })).toBeTruthy()
  })

  it('sends a first-time visitor from the English root to their own language', () => {
    vi.stubGlobal('navigator', { languages: ['ru-RU', 'ru'] } as unknown as Navigator)
    render(<Root route="home" locale="en" />)
    expect(replace).toHaveBeenCalledWith('/ru')
  })

  it('never redirects away from a locale that is already in the URL', () => {
    vi.stubGlobal('navigator', { languages: ['ru-RU'] } as unknown as Navigator)
    render(<Root route="home" locale="de" />)
    expect(replace).not.toHaveBeenCalled()
  })

  it('never redirects once a language was chosen by hand', () => {
    localStorage.setItem(LOCALE_STORAGE_KEY, 'en')
    vi.stubGlobal('navigator', { languages: ['ru-RU'] } as unknown as Navigator)
    render(<Root route="home" locale="en" />)
    expect(replace).not.toHaveBeenCalled()
  })

  it('does not redirect a visitor whose language is already English', () => {
    vi.stubGlobal('navigator', { languages: ['en-GB'] } as unknown as Navigator)
    render(<Root route="home" locale="en" />)
    expect(replace).not.toHaveBeenCalled()
  })

  it('never redirects away from the guide, only from the home page', () => {
    vi.stubGlobal('navigator', { languages: ['ru-RU'] } as unknown as Navigator)
    render(<Root route="methodology" locale="en" />)
    expect(replace).not.toHaveBeenCalled()
  })
})
