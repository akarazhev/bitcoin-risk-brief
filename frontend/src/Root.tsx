import { useEffect } from 'react'
import App from './App'
import Methodology from './Methodology'
import { readStoredLocale } from './localePreference'
import { resolveInitialLocale, type Locale } from './locales'
import { urlPathFor, type RouteName } from './routes'

export function Root({ route, locale }: { route: RouteName; locale: Locale }) {
  useEffect(() => {
    // Only the unprefixed English home guesses. Every other document states its language in the URL,
    // and a visitor who chose by hand is never moved again.
    if (route !== 'home' || locale !== 'en') return
    if (readStoredLocale() !== null) return
    const detected = resolveInitialLocale(navigator?.languages)
    if (detected === 'en') return
    location.replace(urlPathFor('home', detected))
  }, [route, locale])

  return route === 'methodology' ? <Methodology locale={locale} /> : <App locale={locale} />
}

export default Root
