import { supportedLocales, type Locale } from './locales'

export const SITE_ORIGIN = 'https://bitcoinriskbrief.minihub.app'

export type RouteName = 'home' | 'methodology'

export interface SiteDocument {
  route: RouteName
  locale: Locale
  /** Canonical path, no trailing slash except at the root. */
  urlPath: string
  /** Path inside dist/. Flat, so nginx resolves it with try_files $uri $uri.html. */
  filePath: string
}

export function urlPathFor(route: RouteName, locale: Locale): string {
  const prefix = locale === 'en' ? '' : `/${locale}`
  if (route === 'home') return prefix === '' ? '/' : prefix
  return `${prefix}/methodology`
}

function filePathFor(route: RouteName, locale: Locale): string {
  if (route === 'home') return locale === 'en' ? 'index.html' : `${locale}.html`
  return locale === 'en' ? 'methodology.html' : `${locale}/methodology.html`
}

export const siteDocuments: readonly SiteDocument[] = supportedLocales.flatMap((locale) =>
  (['home', 'methodology'] as const).map((route) => ({
    route,
    locale,
    urlPath: urlPathFor(route, locale),
    filePath: filePathFor(route, locale),
  })),
)

export function documentForPath(pathname: string): SiteDocument | undefined {
  return siteDocuments.find((document) => document.urlPath === pathname)
}
