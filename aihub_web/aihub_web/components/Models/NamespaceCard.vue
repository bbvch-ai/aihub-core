<template>
  <div
    class="flex cursor-pointer flex-col gap-3 rounded-xl border border-surface-200 p-4 hover:bg-surface-100 dark:border-surface-800 hover:dark:bg-surface-800"
  >
    <div class="flex items-center justify-between gap-4">
      <div class="flex items-center justify-start gap-2">
        <div
          class="flex items-center justify-center rounded-full bg-white p-3 dark:bg-surface-900"
        >
          <Icon
            :name="getModelIcon(model)"
            size="1.5em"
          />
        </div>
        <h3 class="font-semibold opacity-80">
          {{ model.model_name }}
        </h3>
      </div>
    </div>
    <div>
      <div class="text-sm">
        {{ t('models.costPer1M') }} <span class="font-light">{{
          `$${model.input_cost_per_million_token.toFixed(2)}`
        }} / {{
          `$${model.output_cost_per_million_token.toFixed(2)}`
        }}</span>
      </div>
      <div class="text-sm">
        {{ t('models.tokens') }} <span class="font-light">{{ formatTokenLimits(model) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ModelDTO } from '@core/sdk/client'

defineProps<{
  model: ModelDTO
}>()

const { t } = useI18n()

// Local utility functions
const formatNumber = (num: number): string => {
  return new Intl.NumberFormat().format(num)
}

const formatTokenLimits = (model: ModelDTO): string => {
  const input = model?.max_input_tokens
  const output = model?.max_output_tokens

  if (input && output) {
    return `${formatNumber(input)} / ${formatNumber(output)}`
  }
  else if (input) {
    return `${formatNumber(input)} / -`
  }
  else if (output) {
    return `- / ${formatNumber(output)}`
  }
  return '- / -'
}

const getModelIcon = (model: ModelDTO): string => {
  const mode = model.mode
  switch (mode) {
    case 'chat':
      return 'mdi:chat'
    case 'embedding':
      return 'mdi:vector-triangle'
    case 'image_generation':
      return 'mdi:image'
    case 'audio_transcription':
    case 'audio_speech':
      return 'mdi:microphone'
    default:
      return 'mdi:robot'
  }
}
</script>
