import { copy, getLocaleOption, localeOptions, stateLabel, supportedLocales } from './locales'

test('defines the issue 28 supported locale set in selector order', () => {
  expect(supportedLocales).toEqual(['en', 'ru', 'zh', 'de', 'fr', 'es', 'ar'])
  expect(localeOptions.map((option) => option.code)).toEqual(supportedLocales)
  expect(localeOptions.map((option) => option.shortLabel)).toEqual([
    'EN - English',
    'RU - Русский',
    'ZH - 简体中文',
    'DE - Deutsch',
    'FR - Français',
    'ES - Español',
    'AR - العربية',
  ])
})

test('marks Arabic as RTL and all other supported locales as LTR', () => {
  for (const locale of supportedLocales) {
    expect(getLocaleOption(locale).dir).toBe(locale === 'ar' ? 'rtl' : 'ltr')
  }
  expect(getLocaleOption('zh').lang).toBe('zh-CN')
})

test('keeps UI translation keys complete for every locale', () => {
  const expectedKeys = Object.keys(copy.en).sort()

  for (const locale of supportedLocales) {
    expect(Object.keys(copy[locale]).sort()).toEqual(expectedKeys)
  }
})

test('provides exact localized Turnstile errors and privacy disclosure', () => {
  const expected = {
    en: {
      turnstileError: 'Complete the bot check and try again.',
      turnstileUnavailable: 'Bot verification is temporarily unavailable. Try again shortly.',
      privacyNoteTurnstile: 'Cloudflare Turnstile checks waitlist submissions for automated abuse.',
    },
    ru: {
      turnstileError: 'Пройдите проверку на бота и повторите попытку.',
      turnstileUnavailable: 'Проверка на бота временно недоступна. Повторите попытку чуть позже.',
      privacyNoteTurnstile: 'Cloudflare Turnstile проверяет отправку формы листа ожидания на автоматические злоупотребления.',
    },
    zh: {
      turnstileError: '请完成人机验证后重试。',
      turnstileUnavailable: '人机验证暂时不可用，请稍后重试。',
      privacyNoteTurnstile: 'Cloudflare Turnstile 会检查候补名单提交，以防止自动化滥用。',
    },
    de: {
      turnstileError: 'Schließen Sie die Bot-Prüfung ab und versuchen Sie es erneut.',
      turnstileUnavailable: 'Die Bot-Prüfung ist vorübergehend nicht verfügbar. Versuchen Sie es gleich noch einmal.',
      privacyNoteTurnstile: 'Cloudflare Turnstile prüft Wartelistenanmeldungen auf automatisierten Missbrauch.',
    },
    fr: {
      turnstileError: 'Effectuez la vérification anti-robot puis réessayez.',
      turnstileUnavailable: 'La vérification anti-robot est temporairement indisponible. Réessayez dans un instant.',
      privacyNoteTurnstile: 'Cloudflare Turnstile vérifie les inscriptions à la liste d’attente contre les abus automatisés.',
    },
    es: {
      turnstileError: 'Completa la verificación anti-bot y vuelve a intentarlo.',
      turnstileUnavailable: 'La verificación anti-bot no está disponible temporalmente. Inténtalo de nuevo en breve.',
      privacyNoteTurnstile: 'Cloudflare Turnstile comprueba los envíos a la lista de espera para evitar abusos automatizados.',
    },
    ar: {
      turnstileError: 'أكمل التحقق من الروبوت ثم حاول مرة أخرى.',
      turnstileUnavailable: 'التحقق من الروبوت غير متاح مؤقتا. حاول مرة أخرى بعد قليل.',
      privacyNoteTurnstile: 'يتحقق Cloudflare Turnstile من طلبات قائمة الانتظار لمنع إساءة الاستخدام الآلي.',
    },
  }

  for (const locale of supportedLocales) {
    expect(copy[locale]).toMatchObject(expected[locale])
  }
})

test('localizes core risk-state labels', () => {
  expect(stateLabel('low', 'en')).toBe('Low')
  expect(stateLabel('high', 'ru')).toBe('Высокий')
  expect(stateLabel('neutral', 'zh')).toBe('中性')
  expect(stateLabel('low', 'de')).toBe('Niedrig')
  expect(stateLabel('high', 'fr')).toBe('Élevé')
  expect(stateLabel('neutral', 'es')).toBe('Neutral')
  expect(stateLabel('low', 'ar')).toBe('منخفض')
})

test('preserves unknown risk-state labels', () => {
  expect(stateLabel('watch', 'en')).toBe('watch')
  expect(stateLabel('toString', 'en')).toBe('toString')
})
