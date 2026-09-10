<template>
  <Accordion>
    <AccordionPanel value="0">
      <AccordionHeader class="text-lg font-semibold">
        {{ t('models.modelDetails.additionalInfo') }}
      </AccordionHeader>
      <AccordionContent>
        <div
          v-if="hasAdvancedPricing"
          class="mb-6"
        >
          <h4 class="mb-4 text-base font-semibold">
            {{ t('models.modelDetails.advancedPricing') }}
          </h4>
          <div class="grid grid-cols-3 gap-6">
            <div
              v-for="priceItem in advancedPricingItems"
              :key="priceItem.key"
              class="flex flex-col items-start gap-2"
            >
              <span class="font-semibold">{{ priceItem.label }}</span>
              <span class="text-lg font-light">${{ priceItem.value.toFixed(4) }}</span>
            </div>
          </div>
        </div>

        <div
          v-if="hasRateLimits"
          class="mb-6"
        >
          <h4 class="mb-4 text-base font-semibold">
            {{ t('models.modelDetails.rateLimits') }}
          </h4>
          <div class="grid grid-cols-3 gap-6">
            <div
              v-if="props.model.model_info?.tpm"
              class="flex flex-col items-start gap-2"
            >
              <span class="font-semibold">{{ t('models.modelDetails.tokensPerMinute') }}</span>
              <span class="text-lg font-light">{{ formatNumber(props.model.model_info.tpm) }}</span>
            </div>
            <div
              v-if="props.model.model_info?.rpm"
              class="flex flex-col items-start gap-2"
            >
              <span class="font-semibold">{{ t('models.modelDetails.requestsPerMinute') }}</span>
              <span class="text-lg font-light">{{ formatNumber(props.model.model_info.rpm) }}</span>
            </div>
          </div>
        </div>

        <div
          v-if="hasCapabilities"
          class="mb-6"
        >
          <h4 class="mb-4 text-base font-semibold">
            {{ t('models.modelDetails.capabilities') }}
          </h4>
          <div class="flex flex-wrap gap-2">
            <Badge
              v-for="capability in capabilities"
              :key="capability"
              :value="capability"
              severity="secondary"
              class="text-sm"
            />
          </div>
        </div>

        <div
          v-if="hasOtherDetails"
          class="mb-6"
        >
          <h4 class="mb-4 text-base font-semibold">
            {{ t('models.modelDetails.otherDetails') }}
          </h4>
          <div
            class="grid grid-cols-3 gap-6
"
          >
            <div
              v-if="props.model.model_info?.output_vector_size"
              class="flex flex-col items-start gap-2"
            >
              <span class="text-sm font-medium">{{ t('models.modelDetails.outputVectorSize') }}</span>
              <Tag
                :value="formatNumber(props.model.model_info.output_vector_size)"
                severity="secondary"
              />
            </div>
            <div
              v-if="props.model.model_info?.supports_embedding_image_input !== null"
              class="flex flex-col items-start gap-2"
            >
              <span class="text-sm font-medium">{{ t('models.modelDetails.supportsEmbeddingImageInput') }}</span>
              <Tag
                :value="props.model.model_info?.supports_embedding_image_input ? 'Yes' : 'No'"
                :severity="props.model.model_info?.supports_embedding_image_input ? 'success' : 'secondary'"
              />
            </div>
          </div>
        </div>

        <div v-if="props.model.model_info?.supported_openai_params?.length">
          <h4 class="mb-4 text-base font-semibold">
            {{ t('models.modelDetails.supportedParams') }}
          </h4>
          <div class="flex flex-wrap gap-2">
            <Badge
              v-for="param in props.model.model_info.supported_openai_params"
              :key="param"
              :value="param"
              severity="secondary"
              class="text-sm"
            />
          </div>
        </div>
      </AccordionContent>
    </AccordionPanel>
  </Accordion>
</template>

<script setup lang="ts">
import type { ModelDto } from '@core/sdk/client'

const props = defineProps<{
  model: ModelDto | null
}>()

const { t } = useI18n()

const formatNumber = (num: number): string => {
  return new Intl.NumberFormat().format(num)
}

const capabilities = computed<string[]>(() => {
  const info = props.model?.model_info
  if (!info) return []
  const capabilityMap = {
    supports_system_messages: t('models.modelDetails.supportsSystemMessages'),
    supports_response_schema: t('models.modelDetails.supportsResponseSchema'),
    supports_vision: t('models.modelDetails.supportsVision'),
    supports_function_calling: t('models.modelDetails.supportsFunctionCalling'),
    supports_tool_choice: t('models.modelDetails.supportsToolChoice'),
    supports_assistant_prefill: t('models.modelDetails.supportsAssistantPrefill'),
    supports_prompt_caching: t('models.modelDetails.supportsPromptCaching'),
    supports_audio_input: t('models.modelDetails.supportsAudioInput'),
    supports_audio_output: t('models.modelDetails.supportsAudioOutput'),
    supports_pdf_input: t('models.modelDetails.supportsPdfInput'),
    supports_native_streaming: t('models.modelDetails.supportsNativeStreaming'),
    supports_web_search: t('models.modelDetails.supportsWebSearch'),
    supports_url_context: t('models.modelDetails.supportsUrlContext'),
    supports_reasoning: t('models.modelDetails.supportsReasoning'),
    supports_computer_use: t('models.modelDetails.supportsComputerUse'),
  }

  return Object.keys(capabilityMap)
    .filter(key => info[key as keyof typeof info] != null)
    .map(key => capabilityMap[key as keyof typeof capabilityMap])
})

const advancedPricingItems = computed<Array<{ key: string, label: string, value: number }>>(() => {
  if (!props.model?.model_info) return []

  const info = props.model.model_info
  const items = [
    {
      key: 'cache_creation_input_token_cost',
      label: t('models.modelDetails.cacheCreationCost'),
      value: info.cache_creation_input_token_cost,
    },
    {
      key: 'cache_read_input_token_cost',
      label: t('models.modelDetails.cacheReadCost'),
      value: info.cache_read_input_token_cost,
    },
    {
      key: 'input_cost_per_token_above_128k_tokens',
      label: t('models.modelDetails.inputCostAbove128k'),
      value: info.input_cost_per_token_above_128k_tokens,
    },
    {
      key: 'input_cost_per_token_above_200k_tokens',
      label: t('models.modelDetails.inputCostAbove200k'),
      value: info.input_cost_per_token_above_200k_tokens,
    },
    {
      key: 'input_cost_per_audio_token',
      label: t('models.modelDetails.inputAudioCost'),
      value: info.input_cost_per_audio_token,
    },
    {
      key: 'input_cost_per_token_batches',
      label: t('models.modelDetails.inputBatchCost'),
      value: info.input_cost_per_token_batches,
    },
    {
      key: 'output_cost_per_token_batches',
      label: t('models.modelDetails.outputBatchCost'),
      value: info.output_cost_per_token_batches,
    },
    {
      key: 'output_cost_per_audio_token',
      label: t('models.modelDetails.outputAudioCost'),
      value: info.output_cost_per_audio_token,
    },
    {
      key: 'output_cost_per_reasoning_token',
      label: t('models.modelDetails.reasoningTokenCost'),
      value: info.output_cost_per_reasoning_token,
    },
    {
      key: 'output_cost_per_token_above_128k_tokens',
      label: t('models.modelDetails.outputCostAbove128k'),
      value: info.output_cost_per_token_above_128k_tokens,
    },
    {
      key: 'output_cost_per_token_above_200k_tokens',
      label: t('models.modelDetails.outputCostAbove200k'),
      value: info.output_cost_per_token_above_200k_tokens,
    },
    { key: 'output_cost_per_image', label: t('models.modelDetails.imageCost'), value: info.output_cost_per_image },
    {
      key: 'search_context_cost_per_query_low',
      label: t('models.modelDetails.searchContextCostLow'),
      value: info.search_context_cost_per_query?.search_context_size_low,
    },
    {
      key: 'search_context_cost_per_query_medium',
      label: t('models.modelDetails.searchContextCostMedium'),
      value: info.search_context_cost_per_query?.search_context_size_medium,
    },
    {
      key: 'search_context_cost_per_query_high',
      label: t('models.modelDetails.searchContextCostHigh'),
      value: info.search_context_cost_per_query?.search_context_size_high,
    },
  ]

  return items.filter(item => item.value !== null && item.value !== undefined)
})

const hasAdvancedPricing = computed<boolean>(() => {
  return advancedPricingItems.value.length > 0
})

const hasCapabilities = computed<boolean>(() => {
  return capabilities.value.length > 0
})

const hasRateLimits = computed<boolean>(() => {
  if (!props.model) return false
  return !!(props.model.model_info?.tpm || props.model.model_info?.rpm)
})

const hasOtherDetails = computed<boolean>(() => {
  if (!props.model) return false
  return props.model.model_info?.output_vector_size || props.model.model_info?.supports_embedding_image_input !== null
})
</script>
