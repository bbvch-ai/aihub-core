import AgentSelector from '@core/components/FormKit/AgentSelector.vue'
import ChipsInput from '@core/components/FormKit/ChipsInput.vue'
import CronInput from '@core/components/FormKit/CronInput.vue'
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

// FormKit skips a rule entirely when the node's value is empty, unless the rule opts out —
// which is why the built-in `required` sets this too. Without it the rule would never run on a
// never-touched field, whose value is still `null`, and a blank Name would pass on a fresh
// create form: precisely the case this rule exists to catch.
localeRequired.skipEmpty = false

const localeRequiredMessages = {
  de: 'Mindestens eine Sprache muss ausgefüllt sein.',
  en: 'At least one language must be filled in.',
  fr: 'Au moins une langue doit être renseignée.',
  it: 'Almeno una lingua deve essere compilata.',
}

// Same shape of problem for agentSelector: its value is always an `{agent_class, agent_id}` object,
// so picking a class alone yields a non-empty object with a blank `agent_id` that `required` accepts.
// A blank id then renders as a NATS wildcard at runtime and the delegation reaches no agent at all.
// Backend `AgentSelector` elements emit `agentRefRequired` instead
// (see packages/core/swiss_ai_hub/core/form/elements/agent_selector.py).
function agentRefRequired(node: FormKitNode): boolean {
  const value = node.value as { agent_class?: string | null, agent_id?: string | null } | null | undefined
  if (!value) return false
  return !!value.agent_class?.trim() && !!value.agent_id?.trim()
}

// As with localeRequired: without this the rule never runs on a never-touched field, whose value is
// still `null`, so a fresh create form would submit with no agent selected at all.
agentRefRequired.skipEmpty = false

const agentRefRequiredMessages = {
  de: 'Bitte wählen Sie einen Agententyp und ein Agentenprofil aus.',
  en: 'Please select both an agent type and an agent profile.',
  fr: 'Veuillez sélectionner un type d\'agent et un profil d\'agent.',
  it: 'Seleziona sia un tipo di agente sia un profilo di agente.',
}

const config: DefaultConfigOptions = {
  rules: { localeRequired, agentRefRequired },
  messages: Object.fromEntries(
    LOCALES.map(locale => [locale, {
      validation: {
        localeRequired: localeRequiredMessages[locale],
        agentRefRequired: agentRefRequiredMessages[locale],
      },
    }]),
  ),
  inputs: {
    ...primeInputs,
    agentSelector: createInput(AgentSelector, {
      props: ['startEvent', 'classPlaceholder', 'idPlaceholder', 'filter'],
    }),
    chipsInput: createInput(ChipsInput, {
      props: ['placeholder'],
    }),
    cronInput: createInput(CronInput, {
      props: ['timezonePlaceholder', 'filter'],
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
