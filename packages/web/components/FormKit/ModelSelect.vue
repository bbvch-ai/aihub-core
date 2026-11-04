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

import type { ModelDto } from '@core/sdk/client'

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
  }
}

const props = defineProps<ModelSelectProps>()

// Get custom props from context (FormKit passes them there, not as direct props)
const mode = computed(() => props.context.mode ?? 'chat')
const placeholder = computed(() => props.context.placeholder)
const filter = computed(() => props.context.filter ?? true)
const showClear = computed(() => props.context.showClear ?? false)

const { t } = useI18n()
const { tenantId } = useTenant()
const { formatNumber } = useNumberLocale()

const models = ref<ModelDto[]>([])
const isLoading = ref(false)

const selectedModel = computed({
  get: () => props.context.value ?? null,
  set: (value: string | null) => {
    props.context.node.input(value)
  },
})

const selectedModelEntry = computed(() => models.value.find((model: ModelDto) => model.model_name === selectedModel.value))

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
  try {
    const response = await getLitellmModelsByMode({
      composable: '$fetch',
      path: { tenant_id: tenantId.value!, mode: mode.value },
    })
    models.value = response
  }
  catch (error) {
    console.error(`Failed to fetch models for mode "${mode.value}":`, error)
    models.value = []
  }
  finally {
    isLoading.value = false
  }
}

// Fetch models on mount
onMounted(() => {
  fetchModels()
})

// Refetch if mode changes
watch(mode, () => {
  fetchModels()
})
</script>
