import AgentSelector from '@core/components/FormKit/AgentSelector.vue'
import ChipsInput from '@core/components/FormKit/ChipsInput.vue'
import IconSelector from '@core/components/FormKit/IconSelector.vue'
import KnowledgeDatabaseSelector from '@core/components/FormKit/KnowledgeDatabaseSelector.vue'
import LocaleInput from '@core/components/FormKit/LocaleInput.vue'
import ModelSelect from '@core/components/FormKit/ModelSelect.vue'
import TenantSelect from '@core/components/FormKit/TenantSelect.vue'
import VectorStoreInput from '@core/components/FormKit/VectorStoreInput.vue'
import { en, de, fr, it } from '@formkit/i18n'
import { createInput } from '@formkit/vue'
import { primeInputs } from '@sfxcode/formkit-primevue'

import type { FormKitNode } from '@formkit/core'
import type { DefaultConfigOptions } from '@formkit/vue'

const LOCALES = ['de', 'en', 'fr', 'it'] as const

// FormKit's built-in `required` rule only asks whether a value is present, and a localeInput's
// value is always a `{de, en, fr, it}` object — non-empty, so `required` passes even when every
// locale inside it is blank. Backend `LocaleInput` elements emit `localeRequired` instead
// (see packages/core/swiss_ai_hub/core/form/elements/locale_input.py).
function localeRequired(node: FormKitNode): boolean {
  const value = node.value as Record<string, string | null> | null | undefined
  if (!value) return false
  return LOCALES.some(locale => !!value[locale]?.trim())
}

const localeRequiredMessages = {
  de: 'Mindestens eine Sprache muss ausgefüllt sein.',
  en: 'At least one language must be filled in.',
  fr: 'Au moins une langue doit être renseignée.',
  it: 'Almeno una lingua deve essere compilata.',
}

const config: DefaultConfigOptions = {
  rules: { localeRequired },
  messages: Object.fromEntries(
    LOCALES.map(locale => [locale, { validation: { localeRequired: localeRequiredMessages[locale] } }]),
  ),
  inputs: {
    ...primeInputs,
    agentSelector: createInput(AgentSelector, {
      props: ['startEvent', 'classPlaceholder', 'idPlaceholder', 'filter'],
    }),
    chipsInput: createInput(ChipsInput, {
      props: ['placeholder'],
    }),
    knowledgeDatabaseSelector: createInput(KnowledgeDatabaseSelector, {
      props: ['placeholder', 'filter'],
    }),
    iconSelector: createInput(IconSelector, {
      props: ['options', 'placeholder'],
    }),
    localeInput: createInput(LocaleInput, {
      props: ['inputType', 'rows', 'placeholder'],
    }),
    modelSelect: createInput(ModelSelect, {
      props: ['mode', 'placeholder', 'filter', 'showClear'],
    }),
    tenantSelect: createInput(TenantSelect, {
      props: ['placeholder', 'filter'],
    }),
    vectorStoreInput: createInput(VectorStoreInput, {
      props: ['databasePlaceholder', 'namespacePlaceholder', 'filter'],
    }),
  },
  locales: { en, de, fr, it },
  locale: 'en',
}

export default config
