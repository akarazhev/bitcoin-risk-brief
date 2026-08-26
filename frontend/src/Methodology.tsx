import type { JSX } from 'react'
import { LanguageSelect } from './LanguageSelect'
import { copy, localeOptions, type Locale } from './locales'
import { methodologyCopy } from './methodologyCopy'
import { urlPathFor } from './routes'

const METHODOLOGY_REFERENCE_URL = 'https://docs.bitcoinriskbrief.minihub.app/product/risk-methodology/'

function Methodology({ locale }: { locale: Locale }): JSX.Element {
  const guide = methodologyCopy[locale]
  const labels = copy[locale]

  return (
    <main className="shell methodology-guide">
      <nav className="topbar" aria-label={labels.languageNavigation}>
        <a className="brand" href={urlPathFor('home', locale)}>BTC Risk Brief</a>
        <LanguageSelect
          label={labels.languageSelector}
          locale={locale}
          options={localeOptions}
          route="methodology"
        />
      </nav>

      <article>
        <header>
          <h1>{guide.title}</h1>
          <p className="subtitle">{guide.intro}</p>
          {guide.translationNotice ? <p className="translation-notice">{guide.translationNotice}</p> : null}
        </header>

        {guide.sections.map((section) => (
          <section key={section.heading}>
            <h2>{section.heading}</h2>
            {section.body.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
          </section>
        ))}

        <p>
          <a className="methodology-link" href={METHODOLOGY_REFERENCE_URL}>
            {guide.referenceLinkLabel}
          </a>
        </p>
      </article>
    </main>
  )
}

export default Methodology
