<template>
  <div class="flex flex-col gap-1">
    <Select
      v-model="selectedModel"
      :options="models"
      option-label="display_name"
      option-value="model_name"
      :filter-fields="['display_name', 'model_name']"
      :aria-label="placeholder ?? t('common.selectModel')"
      :placeholder="placeholder ?? t('common.selectModel')"
      :filter="filter"
      :show-clear="showClear"
      :loading="isLoading"
      class="w-full"
    >
      <template #option="{ option }">
        <div class="flex items-center gap-2">
          <Icon
            :name="option.icon"
            size="1.2em"
          />
          <span>{{ option.display_name }}</span>
        </div>
      </template>
      <template #value="{ value }">
        <div
          v-if="value"
          class="flex items-center gap-2"
        >
          <Icon
            :name="selectedModelEntry?.icon ?? 'meteor-icons:cpu'"
            size="1.2em"
          />
          <span>{{ selectedModelEntry?.display_name ?? value }}</span>
        </div>
      </template>
    </Select>
    <Message
      v-if="selectionWarning"
      :severity="loadFailed ? 'error' : 'warn'"
      size="small"
      variant="simple"
    >
      {{ selectionWarning }}
    </Message>
    <!-- FormKit's own help class, as in ModelBoundNumber: each form styles .formkit-help differently. -->
    <!-- eslint-disable tailwindcss/no-custom-classname -->
    <div
      v-if="contextWindow"
      class="formkit-help"
    >
      {{ contextWindow }}
    </div>
    <!-- eslint-enable tailwindcss/no-custom-classname -->
  </div>
</template>

<script setup lang="ts">
import { getLitellmModelsByMode } from '@core/sdk/client'

import type { ModelDto, ModelRequirements } from '@core/sdk/client'

interface ModelSelectProps {
  context: {
    node: {
      input: (value: string | null) => void
    }
    value?: string | null
    attrs: Record<string, unknown>
    // Custom props are passed through context, not as direct Vue props
    mode?: 'chat' | 'embedding' | 'rerank' | 'image_generation' | 'audio_transcription' | 'audio_speech'
    placeholder?: string
    filter?: boolean
    showClear?: boolean
    requirements?: ModelRequirements
  }
}

const props = defineProps<ModelSelectProps>()

// Get custom props from context (FormKit passes them there, not as direct props)
const mode = computed(() => props.context.mode ?? 'chat')
const placeholder = computed(() => props.context.placeholder)
const filter = computed(() => props.context.filter ?? true)
const showClear = computed(() => props.context.showClear ?? false)
const capabilities = computed(() => props.context.requirements?.capabilities ?? [])
const hostingLocations = computed(() => props.context.requirements?.hosting_locations ?? [])
const hasRequirements = computed(() => capabilities.value.length > 0 || hostingLocations.value.length > 0)

const { t } = useI18n()
const { tenantId } = useTenant()
const { formatNumber } = useNumberLocale()
const { modelTypes, modelsAreLoading, error: modelsListError } = useModelsList()

const models = ref<ModelDto[]>([])
// Starts loading, so a stored value is not flagged before the first fetch has said what is selectable.
const isLoading = ref(true)
// A failed fetch says nothing about the stored value or the requirements, so it must not be reported as either.
const fetchFailed = ref(false)

const selectedModel = computed({
  get: () => props.context.value ?? null,
  set: (value: string | null) => {
    props.context.node.input(value)
  },
})

const isSelectable = computed(() => models.value.some((model: ModelDto) => model.model_name === selectedModel.value))

// A stored value the picker no longer offers is still resolved through the unfiltered list, so its name and context
// window stay visible next to the warning that it has to be replaced.
const selectedModelEntry = computed(() => {
  const byName = (model: ModelDto) => model.model_name === selectedModel.value
  return models.value.find(byName) ?? (modelTypes.value ?? []).flatMap(group => group.models).find(byName)
})

// The stored value is looked up in the unfiltered list only when the picker does not offer it; that list failing
// leaves it unknown rather than unavailable.
const loadFailed = computed(() => fetchFailed.value
  || (Boolean(modelsListError.value) && Boolean(selectedModel.value) && !isSelectable.value))

const selectionWarning = computed(() => {
  if (isLoading.value) return null
  if (loadFailed.value) return t('lib.modelSelect.loadFailed')
  if (selectedModel.value && !isSelectable.value && !modelsAreLoading.value) {
    if (!selectedModelEntry.value) return t('lib.modelSelect.unavailable', { model: selectedModel.value })
    const model = selectedModelEntry.value.display_name
    // Such a model fails every picker, whatever it requires, so naming the requirements would mislead.
    return selectedModelEntry.value.model_info.aihub_general_purpose === false
      ? t('lib.modelSelect.specialPurpose', { model })
      : t('lib.modelSelect.notSelectable', { model })
  }
  return hasRequirements.value && models.value.length === 0 ? t('lib.modelSelect.empty') : null
})

// Input and output limits are shown apart, never summed: the sum is the provider's window only for some models.
const contextWindow = computed(() => {
  const info = selectedModelEntry.value?.model_info
  if (!info?.max_input_tokens) return null
  const input = formatNumber(info.max_input_tokens)
  return info.max_output_tokens
    ? t('lib.modelSelect.contextWindow', { input, output: formatNumber(info.max_output_tokens) })
    : t('lib.modelSelect.contextWindowInputOnly', { input })
})

async function fetchModels() {
  isLoading.value = true
  fetchFailed.value = false
  try {
    const response = await getLitellmModelsByMode({
      composable: '$fetch',
      path: { tenant_id: tenantId.value!, mode: mode.value },
      query: { capability: capabilities.value, hosting_location: hostingLocations.value },
    })
    models.value = response
  }
  catch (error) {
    console.error(`Failed to fetch models for mode "${mode.value}":`, error)
    models.value = []
    fetchFailed.value = true
  }
  finally {
    isLoading.value = false
  }
}

// Fetch models on mount
onMounted(() => {
  fetchModels()
})

// Refetch if the mode or the requirements change
watch([mode, () => JSON.stringify(props.context.requirements ?? null)], () => {
  fetchModels()
})
</script>
