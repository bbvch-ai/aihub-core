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

import type { DefaultConfigOptions, PluginConfigs } from '@formkit/vue'

/**
 * Passes when the value is listed in the sibling field named by `address`, or when that list is
 * empty — backend allow-lists treat empty as unrestricted. Reading the sibling through `node.at()`
 * registers it as a validation dependency, so FormKit re-runs this rule when the list itself
 * changes, not only when this field does.
 *
 * Advisory only: it exists so an admin sees the conflict in the form. The backend never depends on
 * it — a value outside the allow-list is rejected where it is actually used.
 */
const memberOf: PluginConfigs['rules'][string] = (node, address: string) => {
  const allowed = node.at(address)?.value
  if (!Array.isArray(allowed) || allowed.length === 0) return true
  return allowed.includes(node.value)
}

const validationMessages: PluginConfigs['messages'] = {
  en: { validation: { memberOf: 'This value is not in the allowed list.' } },
  de: { validation: { memberOf: 'Dieser Wert steht nicht in der Liste der erlaubten Werte.' } },
  fr: { validation: { memberOf: 'Cette valeur ne figure pas dans la liste des valeurs autorisées.' } },
  it: { validation: { memberOf: 'Questo valore non è presente nell\'elenco dei valori consentiti.' } },
}

const config: DefaultConfigOptions = {
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
  rules: { memberOf },
  locales: { en, de, fr, it },
  messages: validationMessages,
  locale: 'en',
}

export default config
