import { renderToString } from 'react-dom/server'
import Root from './Root'
import { buildHead, renderHead } from './head'
import type { Locale } from './locales'
import { siteDocuments, type RouteName } from './routes'

export { siteDocuments } from './routes'

export function renderDocument(route: RouteName, locale: Locale) {
  const fields = buildHead(route, locale)
  return {
    html: renderToString(<Root route={route} locale={locale} />),
    head: renderHead(fields),
    lang: fields.lang,
    dir: fields.dir,
  }
}
