import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { LOCALE_STORAGE_KEY, readStoredLocale, storeLocale } from './localePreference'

beforeEach(() => localStorage.clear())
afterEach(() => vi.unstubAllGlobals())

describe('locale preference', () => {
  it('round-trips a supported locale', () => {
    storeLocale('ru')
    expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBe('ru')
    expect(readStoredLocale()).toBe('ru')
  })

  it('reports no preference when nothing was stored', () => {
    expect(readStoredLocale()).toBeNull()
  })

  it('ignores a stored value that is not a supported locale', () => {
    localStorage.setItem(LOCALE_STORAGE_KEY, 'klingon')
    expect(readStoredLocale()).toBeNull()
  })

  it('survives storage that throws, as private modes do', () => {
    vi.stubGlobal('localStorage', {
      getItem() { throw new Error('denied') },
      setItem() { throw new Error('denied') },
    } as unknown as Storage)
    expect(readStoredLocale()).toBeNull()
    expect(() => storeLocale('de')).not.toThrow()
  })
})
