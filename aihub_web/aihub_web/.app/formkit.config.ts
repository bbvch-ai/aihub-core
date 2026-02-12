import { en, de, fr, it } from '@formkit/i18n'
import { createInput } from '@formkit/vue'
import { primeInputs } from '@sfxcode/formkit-primevue'

import type { DefaultConfigOptions } from '@formkit/vue'

import AgentSelector from '~/components/FormKit/AgentSelector.vue'
import IconSelector from '~/components/FormKit/IconSelector.vue'
import KnowledgeDatabaseSelector from '~/components/FormKit/KnowledgeDatabaseSelector.vue'
import LocaleInput from '~/components/FormKit/LocaleInput.vue'
import ModelSelect from '~/components/FormKit/ModelSelect.vue'
import VectorStoreInput from '~/components/FormKit/VectorStoreInput.vue'

const config: DefaultConfigOptions = {
  inputs: {
    ...primeInputs,
    agentSelector: createInput(AgentSelector, {
      props: ['startEvent', 'classPlaceholder', 'idPlaceholder', 'filter'],
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
