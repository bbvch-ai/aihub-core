// The German, French and Italian UI is Swiss, so numbers are grouped the Swiss way (155’648); every model-bound field
// shares this locale so an input and its hint never show different separators.
const SWISS_NUMBER_LOCALES: Record<string, string> = { de: 'de-CH', fr: 'fr-CH', it: 'it-CH' }

export const useNumberLocale = () => {
  const { locale } = useI18n()
  const numberLocale = computed(() => SWISS_NUMBER_LOCALES[locale.value] ?? locale.value)
  const formatNumber = (value: number, options?: Intl.NumberFormatOptions) =>
    new Intl.NumberFormat(numberLocale.value, options).format(value)

  return { numberLocale, formatNumber }
}
