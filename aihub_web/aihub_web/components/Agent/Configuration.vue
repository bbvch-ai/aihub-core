<template>
  <Panel
    :header="title"
    toggleable
  >
    <p class="text-xs dark:text-surface-500">
      {{ description }}
    </p>
    <div class="content pt-6">
      <FormKit
        id="form"
        v-model="data"
        type="form"
        :submit-label="t('common.actions.save')"
        :submit-attrs="{
          inputClass: 'p-button p-component w-full',
        }"
        :config="{
          validationVisibility: 'blur',
        }"
        @submit="submitHandler"
      >
        <FormKitSchema
          :schema="schema"
          :data="{ ...data }"
        />

        <!-- Render repeaters separately (not supported by FormKit standard) -->
        <FormKitRepeater
          v-for="rep in repeaterElements"
          :key="rep.name"
          v-model="data[rep.name] as Record<string, unknown>[]"
          :name="rep.name"
          :label="rep.label"
          :add-label="rep.addLabel"
          :children-schema="rep.childrenSchema"
          :min="rep.min"
          :max="rep.max"
        />
      </FormKit>
    </div>
  </Panel>
</template>

<script setup lang="ts">
import {
  buildFormKitSchema,
  extractRepeaterConfigs,
  type FormElement,
  type RepeaterConfig,
} from '@core/composables/form/useFormKitTransform'
import { type FormkitElement, getModelsByMode, type GetModelsByModeResponse } from '@core/sdk/client'
import merge from 'lodash/merge'

import type { FormKitSchemaDefinition } from '@formkit/core'

const { t } = useI18n()

const props = defineProps<{
  title: string
  description: string
  form: FormkitElement[]
  initialData?: Record<string, unknown>
}>()

function extractApiModes(elements: FormkitElement[]): string[] {
  const modes = new Set<string>()

  function traverse(el: FormkitElement) {
    const record = el as Record<string, unknown>
    const apiMode = record.options_api_mode || record.optionsApiMode
    if (apiMode && typeof apiMode === 'string') {
      modes.add(apiMode)
    }
    if (record.children && Array.isArray(record.children)) {
      for (const child of record.children as FormkitElement[]) {
        traverse(child)
      }
    }
  }

  for (const el of elements) {
    traverse(el)
  }
  return [...modes]
}

const modelsByMode = ref<Record<string, GetModelsByModeResponse>>({})

async function fetchModelsForModes(modes: string[]) {
  const results: Record<string, GetModelsByModeResponse> = {}
  await Promise.all(
    modes.map(async (mode) => {
      try {
        const models = await getModelsByMode({
          composable: '$fetch',
          path: { mode },
        })
        results[mode] = models
      }
      catch (error) {
        console.warn(`Failed to fetch models for mode "${mode}":`, error)
        results[mode] = []
      }
    }),
  )
  modelsByMode.value = results
}

// Fetch models when form changes
watch(
  () => props.form,
  async (form) => {
    if (form && form.length > 0) {
      const modes = extractApiModes(form)
      if (modes.length > 0) {
        await fetchModelsForModes(modes)
      }
    }
  },
  { immediate: true },
)

const data = ref<Record<string, unknown>>(props.initialData || {})

watch(() => props.initialData, (newData) => {
  if (newData && Object.keys(newData).length > 0) {
    data.value = merge({}, data.value, newData)
  }
}, { deep: true })

const emit = defineEmits<{
  submit: [Record<string, unknown>]
}>()

function createLabelPattern(): RegExp {
  const keys = Object.keys(data.value)
  if (keys.length === 0) return /(?!)/ // Never matches
  return new RegExp(keys.map(key => `\\$${key}`).join('|'), 'g')
}

function replaceLabelVariables(label: string): string {
  const pattern = createLabelPattern()
  return label.replace(pattern, (match: string) => {
    const key = match.substring(1)
    return (data.value[key] as string) || match
  })
}

function resolveApiModeOptions(element: FormElement): unknown[] | undefined {
  const apiMode = element.options_api_mode || element.optionsApiMode
  if (apiMode && typeof apiMode === 'string') {
    const models = modelsByMode.value[apiMode] || []
    return models.map(m => m.model_name)
  }
  return undefined
}

const schema = computed<FormKitSchemaDefinition>(() => {
  return buildFormKitSchema(props.form as FormElement[], {
    labelTransform: replaceLabelVariables,
    optionsResolver: resolveApiModeOptions,
  })
})

const repeaterElements = computed<RepeaterConfig[]>(() => {
  return extractRepeaterConfigs(props.form as FormElement[])
})

async function submitHandler() {
  emit('submit', data.value)
}
</script>

<style scoped>
.content {
  @apply font-light text-xs
}

.content :deep(.formkit-outer) {
  @apply pt-3 pb-1;
}

.content :deep(h1) {
  @apply pt-3 pb-1 text-xl font-bold;
}

.content :deep(h2) {
  @apply pt-3 pb-1 text-lg font-bold;
}

.content :deep(h3) {
  @apply pt-3 pb-1 text-base font-bold;
}

.content :deep(h4) {
  @apply pt-3 pb-1 font-bold;
}

.content :deep(h5) {
  @apply pt-3 pb-1 font-bold;
}

.content :deep(h6) {
  @apply pt-3 pb-1 font-bold;
}

.content :deep(p) {
  @apply pt-3 pb-1 ;
}

.content :deep(blockquote) {
  @apply px-4 py-3 my-4 italic border-s-4 dark:border-gray-500/20 dark:bg-gray-800/20;
}

.content :deep(ul) {
  @apply list-disc list-outside mt-2;
}

.content :deep(ol) {
  @apply list-decimal list-outside mt-2;
}

.content :deep(ul > li) {
  @apply ml-4 mt-2;
}

.content :deep(ol > li) {
  @apply ml-6 mt-2;
}

.content :deep(strong) {
  @apply font-bold;
}

.content :deep(p a) {
  @apply border-b border-dotted border-gray-400  after:content-['↗'] after:pl-[1px];
}

.content :deep(ul a) {
  @apply border-b border-dotted border-gray-400  after:content-['↗'] after:pl-[1px];
}

.content :deep(table) {
  @apply my-8;
}

.content :deep(th) {
  @apply border border-surface-200 dark:border-surface-500 p-2 text-left font-bold bg-surface-100 dark:bg-surface-800;
}

.content :deep(td) {
  @apply border border-surface-200 dark:border-surface-500 p-2 text-left;
}

.content :deep(.formkit-group-fieldset) {
  @apply border border-surface-300 dark:border-surface-600 rounded-lg p-4 mb-4;
}

.content :deep(.formkit-group-fieldset legend) {
  @apply text-sm font-semibold px-2 text-surface-700 dark:text-surface-300;
}

.content :deep(.formkit-group-fieldset .formkit-group-fieldset) {
  @apply ml-2 mt-2;
}

.content :deep(.formkit-slider-value-input) {
  @apply w-20;
}

.content :deep(.formkit-slider-value-input .p-inputnumber-input) {
  @apply text-center text-sm;
}
</style>
