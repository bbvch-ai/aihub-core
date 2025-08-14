<template>
  <StructuralColumn
    :title="t('models.modelDetails.overview')"
    close-route="/service/models"
  >
    <div class="flex flex-col gap-8">
      <Panel class="panel pt-5">
        <div class="grid grid-cols-3 gap-6">
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.name') }}
            </span>
            <span class="text-lg font-light">
              {{ selectedModel?.model_name || t('models.modelDetails.notSpecified') }}
            </span>
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.mode') }}
            </span>
            <span class="text-lg font-light capitalize">
              {{ selectedModel?.model_info?.mode || t('models.modelDetails.notSpecified') }}
            </span>
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.maxInputTokens') }}
            </span>
            <span class="text-lg font-light">
              {{
                model?.model_info?.max_input_tokens ? formatNumber(model?.model_info?.max_input_tokens) : t('models.modelDetails.notSpecified')
              }}
            </span>
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.maxOutputTokens') }}
            </span>
            <span class="text-lg font-light">
              {{
                model?.model_info?.max_output_tokens ? formatNumber(model?.model_info?.max_output_tokens) : t('models.modelDetails.notSpecified')
              }}
            </span>
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.basicInputCost') }}
            </span>
            <span class="text-lg font-light">
              {{
                model?.model_info?.input_cost_per_token !== null && model?.model_info?.input_cost_per_token !== undefined ? `$${model.model_info.input_cost_per_token.toFixed(2)}` : t('models.modelDetails.notSpecified')
              }}
            </span>
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.basicOutputCost') }}
            </span>
            <span class="text-lg font-light">
              {{
                model?.model_info?.output_cost_per_token !== null && model?.model_info?.output_cost_per_token !== undefined ? `$${model.model_info.output_cost_per_token.toFixed(2)}` : t('models.modelDetails.notSpecified')
              }}
            </span>
          </div>
        </div>
      </Panel>

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
                  v-if="model?.model_info?.cache_creation_input_token_cost"
                  class="flex flex-col items-start gap-2"
                >
                  <span class="font-semibold">{{ t('models.modelDetails.cacheCreationCost') }}</span>
                  <span class="text-lg font-light">${{ model.model_info.cache_creation_input_token_cost.toFixed(4) }}</span>
                </div>
                <div
                  v-if="model?.model_info?.cache_read_input_token_cost"
                  class="flex flex-col items-start gap-2"
                >
                  <span class="font-semibold">{{ t('models.modelDetails.cacheReadCost') }}</span>
                  <span class="text-lg font-light">${{ model.model_info.cache_read_input_token_cost.toFixed(4) }}</span>
                </div>
                <div
                  v-if="model?.model_info?.input_cost_per_token_above_128k_tokens"
                  class="flex flex-col items-start gap-2"
                >
                  <span class="font-semibold">{{ t('models.modelDetails.inputCostAbove128k') }}</span>
                  <span class="text-lg font-light">${{ model.model_info.input_cost_per_token_above_128k_tokens.toFixed(4) }}</span>
                </div>
                <div
                  v-if="model?.model_info?.input_cost_per_token_above_200k_tokens"
                  class="flex flex-col items-start gap-2"
                >
                  <span class="font-semibold">{{ t('models.modelDetails.inputCostAbove200k') }}</span>
                  <span class="text-lg font-light">${{ model.model_info.input_cost_per_token_above_200k_tokens.toFixed(4) }}</span>
                </div>
                <div
                  v-if="model?.model_info?.input_cost_per_audio_token"
                  class="flex flex-col items-start gap-2"
                >
                  <span class="font-semibold">{{ t('models.modelDetails.inputAudioCost') }}</span>
                  <span class="text-lg font-light">${{ model.model_info.input_cost_per_audio_token.toFixed(4) }}</span>
                </div>
                <div
                  v-if="model?.model_info?.input_cost_per_token_batches"
                  class="flex flex-col items-start gap-2"
                >
                  <span class="font-semibold">{{ t('models.modelDetails.inputBatchCost') }}</span>
                  <span class="text-lg font-light">${{ model.model_info.input_cost_per_token_batches.toFixed(4) }}</span>
                </div>
                <div
                  v-if="model?.model_info?.output_cost_per_token_batches"
                  class="flex flex-col items-start gap-2"
                >
                  <span class="font-semibold">{{ t('models.modelDetails.outputBatchCost') }}</span>
                  <span class="text-lg font-light">${{ model.model_info.output_cost_per_token_batches.toFixed(4) }}</span>
                </div>
                <div
                  v-if="model?.model_info?.output_cost_per_audio_token"
                  class="flex flex-col items-start gap-2"
                >
                  <span class="font-semibold">{{ t('models.modelDetails.outputAudioCost') }}</span>
                  <span class="text-lg font-light">${{ model.model_info.output_cost_per_audio_token.toFixed(4) }}</span>
                </div>
                <div
                  v-if="model?.model_info?.output_cost_per_reasoning_token"
                  class="flex flex-col items-start gap-2"
                >
                  <span class="font-semibold">{{ t('models.modelDetails.reasoningTokenCost') }}</span>
                  <span class="text-lg font-light">${{ model.model_info.output_cost_per_reasoning_token.toFixed(4) }}</span>
                </div>
                <div
                  v-if="model?.model_info?.output_cost_per_token_above_128k_tokens"
                  class="flex flex-col items-start gap-2"
                >
                  <span class="font-semibold">{{ t('models.modelDetails.outputCostAbove128k') }}</span>
                  <span class="text-lg font-light">${{
                    model.model_info.output_cost_per_token_above_128k_tokens.toFixed(4)
                  }}</span>
                </div>
                <div
                  v-if="model?.model_info?.output_cost_per_token_above_200k_tokens"
                  class="flex flex-col items-start gap-2"
                >
                  <span class="font-semibold">{{ t('models.modelDetails.outputCostAbove200k') }}</span>
                  <span class="text-lg font-light">${{
                    model.model_info.output_cost_per_token_above_200k_tokens.toFixed(4)
                  }}</span>
                </div>
                <div
                  v-if="model?.model_info?.output_cost_per_image"
                  class="flex flex-col items-start gap-2"
                >
                  <span class="font-semibold">{{ t('models.modelDetails.imageCost') }}</span>
                  <span class="text-lg font-light">${{ model.model_info.output_cost_per_image.toFixed(4) }}</span>
                </div>
                <div
                  v-if="model?.model_info?.search_context_cost_per_query"
                  class="flex flex-col items-start gap-2"
                >
                  <span class="font-semibold">{{ t('models.modelDetails.searchContextCost') }}</span>
                  <span class="text-lg font-light">${{ model.model_info.search_context_cost_per_query.toFixed(4) }}</span>
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
                  v-if="model?.model_info?.tpm"
                  class="flex flex-col items-start gap-2"
                >
                  <span class="font-semibold">{{ t('models.modelDetails.tokensPerMinute') }}</span>
                  <span class="text-lg font-light">{{ formatNumber(model.model_info.tpm) }}</span>
                </div>
                <div
                  v-if="model?.model_info?.rpm"
                  class="flex flex-col items-start gap-2"
                >
                  <span class="font-semibold">{{ t('models.modelDetails.requestsPerMinute') }}</span>
                  <span class="text-lg font-light">{{ formatNumber(model.model_info.rpm) }}</span>
                </div>
              </div>
            </div>

            <div class="mb-6">
              <h4 class="mb-4 text-base font-semibold">
                {{ t('models.modelDetails.capabilities') }}
              </h4>
              <div class="flex flex-wrap gap-2">
                <Badge
                  v-if="model?.model_info?.supports_system_messages !== null"
                  :value="t('models.modelDetails.supportsSystemMessages')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.model_info?.supports_response_schema !== null"
                  :value="t('models.modelDetails.supportsResponseSchema')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.model_info?.supports_vision !== null"
                  :value="t('models.modelDetails.supportsVision')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.model_info?.supports_function_calling !== null"
                  :value="t('models.modelDetails.supportsFunctionCalling')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.model_info?.supports_tool_choice !== null"
                  :value="t('models.modelDetails.supportsToolChoice')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.model_info?.supports_assistant_prefill !== null"
                  :value="t('models.modelDetails.supportsAssistantPrefill')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.model_info?.supports_prompt_caching !== null"
                  :value="t('models.modelDetails.supportsPromptCaching')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.model_info?.supports_audio_input !== null"
                  :value="t('models.modelDetails.supportsAudioInput')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.model_info?.supports_audio_output !== null"
                  :value="t('models.modelDetails.supportsAudioOutput')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.model_info?.supports_pdf_input !== null"
                  :value="t('models.modelDetails.supportsPdfInput')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.model_info?.supports_native_streaming !== null"
                  :value="t('models.modelDetails.supportsNativeStreaming')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.model_info?.supports_web_search !== null"
                  :value="t('models.modelDetails.supportsWebSearch')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.model_info?.supports_url_context !== null"
                  :value="t('models.modelDetails.supportsUrlContext')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.model_info?.supports_reasoning !== null"
                  :value="t('models.modelDetails.supportsReasoning')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.model_info?.supports_computer_use !== null"
                  :value="t('models.modelDetails.supportsComputerUse')"
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
                  v-if="model?.model_info?.output_vector_size"
                  class="flex flex-col items-start gap-2"
                >
                  <span class="text-sm font-medium">{{ t('models.modelDetails.outputVectorSize') }}</span>
                  <Tag
                    :value="formatNumber(model.model_info.output_vector_size)"
                    severity="secondary"
                  />
                </div>
                <div
                  v-if="model?.model_info?.supports_embedding_image_input !== null"
                  class="flex flex-col items-start gap-2"
                >
                  <span class="text-sm font-medium">{{ t('models.modelDetails.supportsEmbeddingImageInput') }}</span>
                  <Tag
                    :value="model?.model_info?.supports_embedding_image_input ? 'Yes' : 'No'"
                    :severity="model?.model_info?.supports_embedding_image_input ? 'success' : 'secondary'"
                  />
                </div>
              </div>
            </div>

            <div v-if="model?.model_info?.supported_openai_params?.length">
              <h4 class="mb-4 text-base font-semibold">
                {{ t('models.modelDetails.supportedParams') }}
              </h4>
              <div class="flex flex-wrap gap-2">
                <Badge
                  v-for="param in model.model_info.supported_openai_params"
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
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
import type { ModelDTO } from '@core/sdk/client'

const route = useRoute()
const { t } = useI18n()
const { modelTypes } = useModelsList()

const props = defineProps<{
  model: ModelDTO
}>()

const formatNumber = (num: number): string => {
  return new Intl.NumberFormat().format(num)
}

const selectedModel = computed(() => {
  if (!modelTypes.value) return null

  const modelName = decodeURIComponent(route.params?.model_name as string)

  for (const modelType of modelTypes.value) {
    const model = modelType.models.find((m: ModelDTO) => m?.model_name === modelName)
    if (model) return model
  }

  return null
})

const model = computed(() => selectedModel.value || props.model)

const hasAdvancedPricing = computed(() => {
  if (!model.value) return false
  return !!(model.value.model_info.cache_creation_input_token_cost
    || model.value.model_info.cache_read_input_token_cost
    || model.value.model_info.input_cost_per_token_above_128k_tokens
    || model.value.model_info.input_cost_per_token_above_200k_tokens
    || model.value.model_info.input_cost_per_audio_token
    || model.value.model_info.input_cost_per_token_batches
    || model.value.model_info.output_cost_per_token_batches
    || model.value.model_info.output_cost_per_audio_token
    || model.value.model_info.output_cost_per_reasoning_token
    || model.value.model_info.output_cost_per_token_above_128k_tokens
    || model.value.model_info.output_cost_per_token_above_200k_tokens
    || model.value.model_info.output_cost_per_image
    || model.value.model_info.search_context_cost_per_query)
})

const hasRateLimits = computed(() => {
  if (!model.value) return false
  return !!(model.value.model_info.tpm || model.value.model_info.rpm)
})

const hasOtherDetails = computed(() => {
  if (!model.value) return false
  return model.value.model_info.output_vector_size || model.value.model_info.supports_embedding_image_input !== null
})
</script>
