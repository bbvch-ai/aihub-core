<template>
  <div>
    <!-- Language Selector and Translate Button -->
    <div class="mb-2 flex items-center gap-2">
      <SelectButton
        v-model="activeLocale"
        :options="localeOptions"
        option-label="label"
        option-value="value"
        :allow-empty="false"
        size="small"
      >
        <template #option="{ option }">
          <span>{{ option.label }}</span>
          <!-- Filled indicator dot -->
          <span
            v-if="hasValue(option.value)"
            class="absolute bottom-0.5 left-1/2 size-1 -translate-x-1/2 rounded-full bg-green-500"
          />
        </template>
      </SelectButton>

      <!-- Translate Button -->
      <Button
        v-if="canTranslate"
        v-tooltip.top="t('form.locale_input.translate_tooltip')"
        :loading="isTranslating"
        :disabled="isTranslating"
        icon="pi pi-language"
        size="small"
        severity="secondary"
        text
        @click="handleTranslate"
      />
    </div>

    <!-- Text Input (single line) -->
    <div class="relative">
      <InputText
        v-if="inputType === 'text'"
        v-model="currentValue"
        :placeholder="localizedPlaceholder"
        :maxlength="maxLength"
        class="w-full"
      />

      <!-- Textarea (multi-line) -->
      <Textarea
        v-else
        v-model="currentValue"
        :aria-label="localizedPlaceholder"
        :placeholder="localizedPlaceholder"
        :rows="rows"
        :maxlength="maxLength"
        class="w-full"
      />

      <!-- Loading overlay -->
      <div
        v-if="isTranslating"
        class="absolute inset-0 flex items-center justify-center rounded bg-surface-100/80 dark:bg-surface-800/80"
      >
        <i class="pi pi-spin pi-spinner text-xl" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { LocaleString } from '@core/sdk/client'

interface LocaleInputProps {
  context: {
    node: {
      input: (value: LocaleString) => void
    }
    value?: LocaleString
    attrs: Record<string, unknown>
    // Custom props are passed through context, not as direct Vue props
    inputType?: 'text' | 'textarea'
    rows?: number
    placeholder?: LocaleString
    allowTranslation?: boolean
    maxLength?: number
  }
}

const props = defineProps<LocaleInputProps>()
const { t } = useI18n()
const toast = useToast()
const { translate, isTranslating } = useTranslate()
const { tenantId } = useTenant()

// Get custom props from context (FormKit passes them there, not as direct props)
const inputType = computed(() => props.context.inputType ?? 'text')
const rows = computed(() => props.context.rows ?? 3)
const placeholder = computed(() => props.context.placeholder)
const maxLength = computed(() => props.context.maxLength)

const locales = ['de', 'en', 'fr', 'it'] as const
type Locale = (typeof locales)[number]

const localeOptions = locales.map(lang => ({
  label: lang.toUpperCase(),
  value: lang,
}))

const activeLocale = ref<Locale>('en')

function isLocale(value: unknown): value is Locale {
  return locales.includes(value as Locale)
}

// Get the current locale string value
const localeValue = computed<LocaleString>(() => {
  return props.context.value ?? { de: null, en: null, fr: null, it: null }
})

// Current input value for the active locale
// The guard is belt-and-braces next to `:allow-empty="false"`: with an unset `activeLocale`
// this setter used to write under the key `"null"`, producing a value whose four locales
// were all empty but which no longer looked like a locale object to the backend's
// normalization — so it slipped past validation and saved a blank name (issue #135).
const currentValue = computed({
  get: () => (isLocale(activeLocale.value) ? localeValue.value[activeLocale.value] ?? '' : ''),
  set: (newVal: string) => {
    if (!isLocale(activeLocale.value)) return
    const updated: LocaleString = {
      ...localeValue.value,
      [activeLocale.value]: newVal || null,
    }
    props.context.node.input(updated)
  },
})

// Get localized placeholder for current locale
const localizedPlaceholder = computed(() => {
  if (!placeholder.value) return undefined
  return placeholder.value[activeLocale.value] ?? placeholder.value.en ?? ''
})

function hasValue(lang: Locale): boolean {
  const val = localeValue.value[lang]
  return val !== null && val !== undefined && val !== ''
}

// Check if translation is possible (current locale has text and at least one other locale is empty)
const canTranslate = computed(() => {
  if (props.context.allowTranslation === false) return false
  const currentText = localeValue.value[activeLocale.value]
  if (!currentText) return false

  // Check if any other locale is missing a value
  return locales.some(lang => lang !== activeLocale.value && !hasValue(lang))
})

function notifyTranslationFailed() {
  toast.add({
    severity: 'error',
    summary: t('form.locale_input.translate_failed_summary'),
    detail: t('form.locale_input.translate_failed_detail'),
    life: 6000,
  })
}

// Merged into the value as it is now, not as it was sent: a large prompt takes a minute to translate,
// and anything typed meanwhile must survive.
function applyTranslations(translated: LocaleString, translatedLocales: Locale[]) {
  const updated: LocaleString = { ...localeValue.value }
  for (const lang of translatedLocales) {
    if (!hasValue(lang)) updated[lang] = translated[lang] ?? null
  }
  props.context.node.input(updated)
}

// The backend fills in only the empty locales, each separately, so a partial result is worth applying
// and a retry translates just the ones still missing.
async function handleTranslate() {
  const sourceLocale = activeLocale.value
  const requestedLocales = locales.filter(lang => lang !== sourceLocale && !hasValue(lang))
  try {
    const response = await translate({
      request: {
        text: localeValue.value,
        source_locale: sourceLocale,
      },
      tenantId: tenantId.value!,
    })
    const failedLocales = response.failed_locales ?? []
    const translatedLocales = requestedLocales.filter(lang => !failedLocales.includes(lang))
    if (translatedLocales.length === 0) {
      notifyTranslationFailed()
      return
    }
    applyTranslations(response.translated, translatedLocales)
    if (failedLocales.length > 0) {
      toast.add({
        severity: 'warn',
        summary: t('form.locale_input.translate_partial_summary'),
        detail: t('form.locale_input.translate_partial_detail', {
          locales: failedLocales.map(lang => lang.toUpperCase()).join(', '),
        }),
        life: 6000,
      })
    }
  }
  catch (error) {
    console.error('Failed to translate:', error)
    notifyTranslationFailed()
  }
}
</script>
