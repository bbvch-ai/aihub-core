import AgentSelector from '@core/components/FormKit/AgentSelector.vue'
import ChipsInput from '@core/components/FormKit/ChipsInput.vue'
import IconSelector from '@core/components/FormKit/IconSelector.vue'
import KnowledgeDatabaseSelector from '@core/components/FormKit/KnowledgeDatabaseSelector.vue'
import LocaleInput from '@core/components/FormKit/LocaleInput.vue'
import ModelSelect from '@core/components/FormKit/ModelSelect.vue'
import VectorStoreInput from '@core/components/FormKit/VectorStoreInput.vue'
import { en, de, fr, it } from '@formkit/i18n'
import { createInput } from '@formkit/vue'
import { primeInputs } from '@sfxcode/formkit-primevue'

import type { DefaultConfigOptions } from '@formkit/vue'

const config: DefaultConfigOptions = {
  inputs: {
    ...primeInputs,
    orgMemoryTenantInput: primeInputs.primeInputText,
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
    vectorStoreInput: createInput(VectorStoreInput, {
      props: ['databasePlaceholder', 'namespacePlaceholder', 'filter'],
    }),
  },
  locales: { en, de, fr, it },
  locale: 'en',
}

export default config
