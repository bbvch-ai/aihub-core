<template>
  <div class="content">
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
        :key="rep.path"
        :model-value="getRepeaterData(rep.path)"
        :name="rep.name"
        :label="rep.label"
        :add-label="rep.addLabel"
        :children-schema="rep.childrenSchema"
        :default-item="rep.defaultItem"
        :min="rep.min"
        :max="rep.max"
        @update:model-value="setRepeaterData(rep.path, $event)"
      />
    </FormKit>
  </div>
</template>

<script setup lang="ts">
import {
  buildFormKitSchema,
  extractRepeaterConfigs,
  getNestedValue,
  hydrateFormData,
  serializeFormData,
  setNestedValue,
  type FormElement,
  type RepeaterConfig,
} from '@core/composables/form/useFormKitTransform'
import { cloneDeep } from 'lodash-es'

import type { FormkitElement } from '@core/sdk/client'
import type { FormKitSchemaDefinition } from '@formkit/core'

const { t } = useI18n()

const props = defineProps<{
  form: FormkitElement[]
  initialData?: Record<string, unknown>
}>()

// Clone before hydrating so the form model never shares object references with the
// Pinia-Colada query cache (`initialData` is the live cached `agent_config.configuration`).
// Without the clone, FormKit's write-backs into `data` mutate the cached object, which a
// `deep` watcher here would observe and re-hydrate from — an infinite loop that freezes the
// tab after a save refetch.
function hydrate(raw: Record<string, unknown>): Record<string, unknown> {
  return hydrateFormData(cloneDeep(raw), props.form as FormElement[])
}

const data = ref<Record<string, unknown>>(hydrate(props.initialData || {}))

watch(() => props.initialData, (newData) => {
  if (newData && Object.keys(newData).length > 0) {
    data.value = hydrate(newData)
  }
})

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

const schema = computed<FormKitSchemaDefinition>(() => {
  return buildFormKitSchema(props.form as FormElement[], {
    labelTransform: replaceLabelVariables,
  })
})

const repeaterElements = computed<RepeaterConfig[]>(() => {
  return extractRepeaterConfigs(props.form as FormElement[])
})

function getRepeaterData(path: string): Record<string, unknown>[] {
  return getNestedValue(data.value, path)
}

function setRepeaterData(path: string, value: Record<string, unknown>[]): void {
  setNestedValue(data.value, path, value)
}

async function submitHandler() {
  emit('submit', serializeFormData(data.value, props.form as FormElement[]))
}
</script>

<style scoped>
.content {
  @apply font-light text-xs
}

.content :deep(form) {
  @apply gap-6;
}

.content :deep(.formkit-help) {
  @apply text-xs font-light text-surface-500 dark:text-surface-400;
}

.content :deep(.formkit-outer) {
  @apply pt-3 pb-1;
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
