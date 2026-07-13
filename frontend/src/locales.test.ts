import { copy, getLocaleOption, localeOptions, stateLabel, supportedLocales } from './locales'

test('defines the issue 28 supported locale set in selector order', () => {
  expect(supportedLocales).toEqual(['en', 'ru', 'zh', 'de', 'fr', 'es', 'ar'])
  expect(localeOptions.map((option) => option.code)).toEqual(supportedLocales)
  expect(localeOptions.map((option) => option.shortLabel)).toEqual(['EN', 'RU', '中文', 'DE', 'FR', 'ES', 'AR'])
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
