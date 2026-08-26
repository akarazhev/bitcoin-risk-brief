import { supportedLocales, type Locale } from './locales'

export const LOCALE_STORAGE_KEY = 'brb.locale'

function isLocale(value: string | null): value is Locale {
  return value !== null && (supportedLocales as readonly string[]).includes(value)
}

export function readStoredLocale(): Locale | null {
  try {
    const stored = localStorage.getItem(LOCALE_STORAGE_KEY)
    return isLocale(stored) ? stored : null
  } catch {
    // Private browsing can throw on access. No preference is the safe answer.
    return null
  }
}

export function storeLocale(locale: Locale): void {
  try {
    localStorage.setItem(LOCALE_STORAGE_KEY, locale)
  } catch {
    // A failed write only means the automatic hop may run again. Navigation still happens.
  }
}
