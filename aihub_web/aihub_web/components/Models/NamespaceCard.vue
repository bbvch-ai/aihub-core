<template>
  <div
    class="flex cursor-pointer flex-col gap-3 rounded-xl border border-surface-200 p-5 hover:bg-surface-100 dark:border-surface-800 hover:dark:bg-surface-800"
  >
    <div class="flex items-center gap-4">
      <div
        class="flex items-center justify-center rounded-full bg-white p-3 dark:bg-surface-900"
      >
        <Icon
          :name="props.model.icon"
          size="1.5em"
        />
      </div>
      <div class="flex-1">
        <h3 class="font-semibold opacity-80">
          {{ props.model.model_name }}
        </h3>
        <div class="mt-3 flex flex-col gap-2">
          <div class="flex items-center gap-2">
            <span class="text-sm font-bold text-surface-600 dark:text-surface-400">
              {{ t('models.card.costPer1M') }}:
            </span>
            <span class="text-sm font-light text-surface-900 dark:text-surface-100">
              ${{ inputCostPerToken }}
              <span class="mx-1 text-surface-500">•</span>
              ${{ outputCostPerToken }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-sm font-bold text-surface-600 dark:text-surface-400">
              {{ t('models.card.tokens') }}:
            </span>
            <span class="text-sm font-light text-surface-900 dark:text-surface-100">
              {{ formatTokenLimits }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ModelDtoReadable } from '@core/sdk/client'

const props = defineProps<{
  model: ModelDtoReadable
}>()

const { t } = useI18n()

const formatNumber = (num: number): string => {
  return new Intl.NumberFormat().format(num)
}

const formatTokenLimits = computed<string>(() => {
  const input = props.model?.model_info?.max_input_tokens
  const output = props.model?.model_info?.max_output_tokens

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
})

const inputCostPerToken = computed<string | number>(() => {
  return props.model?.model_info?.input_cost_per_token?.toFixed(2) ?? '-'
})

const outputCostPerToken = computed<string | number>(() => {
  return props.model?.model_info?.output_cost_per_token?.toFixed(2) ?? '-'
})
</script>
