<template>
  <Select
    v-model="selectedModel"
    :options="models"
    option-label="model_name"
    option-value="model_name"
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
        <span>{{ option.model_name }}</span>
      </div>
    </template>
    <template #value="{ value }">
      <div
        v-if="value"
        class="flex items-center gap-2"
      >
        <Icon
          :name="getModelIcon(value)"
          size="1.2em"
        />
        <span>{{ value }}</span>
      </div>
    </template>
  </Select>
</template>

<script setup lang="ts">
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

const { models: fetchedModels, modelsAreLoading: isLoading } = useModelsByMode(mode)
const models = computed<ModelDto[]>(() => fetchedModels.value ?? [])

const selectedModel = computed({
  get: () => props.context.value ?? null,
  set: (value: string | null) => {
    props.context.node.input(value)
  },
})

function getModelIcon(modelName: string): string {
  const model = models.value.find(m => m.model_name === modelName)
  return model?.icon ?? 'meteor-icons:cpu'
}
</script>
