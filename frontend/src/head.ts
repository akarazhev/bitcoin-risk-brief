import { copy, getLocaleOption, supportedLocales, type Locale } from './locales'
import { SITE_ORIGIN, urlPathFor, type RouteName } from './routes'

export interface Alternate {
  hreflang: string
  href: string
}

export interface HeadFields {
  title: string
  description: string
  canonical: string
  lang: string
  dir: 'ltr' | 'rtl'
  alternates: Alternate[]
  jsonLd: string
}

function absolute(route: RouteName, locale: Locale): string {
  const path = urlPathFor(route, locale)
  return path === '/' ? `${SITE_ORIGIN}/` : `${SITE_ORIGIN}${path}`
}

function escapeAttribute(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('"', '&quot;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
}

export function buildHead(route: RouteName, locale: Locale): HeadFields {
  const option = getLocaleOption(locale)
  const t = copy[locale]
  const alternates: Alternate[] = supportedLocales.map((other) => ({
    hreflang: getLocaleOption(other).lang,
    href: absolute(route, other),
  }))
  alternates.push({ hreflang: 'x-default', href: absolute(route, 'en') })

  return {
    title: route === 'home' ? t.headTitle : t.headTitleMethodology,
    description: route === 'home' ? t.headDescription : t.headDescriptionMethodology,
    canonical: absolute(route, locale),
    lang: option.lang,
    dir: option.dir,
    alternates,
    jsonLd: JSON.stringify(
      route === 'home'
        ? {
            '@context': 'https://schema.org',
            '@type': 'WebSite',
            name: 'Bitcoin Risk Brief',
            url: `${SITE_ORIGIN}/`,
            inLanguage: option.lang,
          }
        : {
            '@context': 'https://schema.org',
            '@type': 'TechArticle',
            headline: t.headTitleMethodology,
            url: absolute('methodology', locale),
            inLanguage: option.lang,
            isAccessibleForFree: true,
          },
    ),
  }
}

export function renderHead(fields: HeadFields): string {
  const lines = [
    `<title>${escapeAttribute(fields.title)}</title>`,
    `<meta name="description" content="${escapeAttribute(fields.description)}" />`,
    `<link rel="canonical" href="${escapeAttribute(fields.canonical)}" />`,
    `<meta property="og:title" content="${escapeAttribute(fields.title)}" />`,
    `<meta property="og:description" content="${escapeAttribute(fields.description)}" />`,
    `<meta property="og:url" content="${escapeAttribute(fields.canonical)}" />`,
  ]
  for (const alternate of fields.alternates) {
    lines.push(
      `<link rel="alternate" hreflang="${escapeAttribute(alternate.hreflang)}" href="${escapeAttribute(alternate.href)}" />`,
    )
  }
  lines.push(`<script type="application/ld+json">${fields.jsonLd}</script>`)
  return lines.join('\n    ')
}
