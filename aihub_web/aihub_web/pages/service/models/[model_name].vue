<template>
  <StructuralColumn
    :title="t('models.modelDetails.overview')"
    close-route="/service/models"
  >
    <div class="flex flex-col gap-8">
      <span class="mb-4 block text-sm text-surface-500 dark:text-surface-400">
        {{ selectedModel?.description || t('models.modelDetails.no_description') }}
      </span>

      <Panel class="panel pt-5">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.overview.name') }}
            </span>
            <span class="text-lg font-light">
              {{ selectedModel?.model_name || t('models.modelDetails.notSpecified') }}
            </span>
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.overview.mode') }}
            </span>
            <span class="text-lg font-light capitalize">
              {{ selectedModel?.mode || t('models.modelDetails.notSpecified') }}
            </span>
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.overview.status') }}
            </span>
            <Tag
              :value="selectedModel?.status || 'available'"
              :severity="(selectedModel?.status || 'available') === 'available' ? 'success' : 'error'"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.maxInputTokens') }}
            </span>
            <span class="text-lg font-light">
              {{
                model?.max_input_tokens ? formatNumber(model.max_input_tokens) : t('models.modelDetails.notSpecified')
              }}
            </span>
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.maxOutputTokens') }}
            </span>
            <span class="text-lg font-light">
              {{
                model?.max_output_tokens ? formatNumber(model.max_output_tokens) : t('models.modelDetails.notSpecified')
              }}
            </span>
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.basicInputCost') }}
            </span>
            <span class="text-lg font-light">
              {{
                model?.input_cost_per_million_token !== null && model?.input_cost_per_million_token !== undefined ? `$${model.input_cost_per_million_token.toFixed(2)}` : t('models.modelDetails.notSpecified')
              }}
            </span>
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.basicOutputCost') }}
            </span>
            <span class="text-lg font-light">
              {{
                model?.output_cost_per_million_token !== null && model?.output_cost_per_million_token !== undefined ? `$${model.output_cost_per_million_token.toFixed(2)}` : t('models.modelDetails.notSpecified')
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


            <div v-if="hasAdvancedPricing" class="mb-6">
              <h4 class="text-md font-semibold mb-4">{{ t('models.modelDetails.advancedPricing') }}</h4>
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div v-if="model?.cache_creation_input_token_cost" class="flex flex-col items-start gap-2">
                  <span class="font-semibold">{{ t('models.modelDetails.cacheCreationCost') }}</span>
                  <span class="text-lg font-light">${{ model.cache_creation_input_token_cost.toFixed(4) }}</span>
                </div>
                <div v-if="model?.cache_read_input_token_cost" class="flex flex-col items-start gap-2">
                  <span class="font-semibold">{{ t('models.modelDetails.cacheReadCost') }}</span>
                  <span class="text-lg font-light">${{ model.cache_read_input_token_cost.toFixed(4) }}</span>
                </div>
                <div v-if="model?.input_cost_per_token_above_128k_tokens" class="flex flex-col items-start gap-2">
                  <span class="font-semibold">{{ t('models.modelDetails.inputCostAbove128k') }}</span>
                  <span class="text-lg font-light">${{ model.input_cost_per_token_above_128k_tokens.toFixed(4) }}</span>
                </div>
                <div v-if="model?.input_cost_per_token_above_200k_tokens" class="flex flex-col items-start gap-2">
                  <span class="font-semibold">{{ t('models.modelDetails.inputCostAbove200k') }}</span>
                  <span class="text-lg font-light">${{ model.input_cost_per_token_above_200k_tokens.toFixed(4) }}</span>
                </div>
                <div v-if="model?.input_cost_per_audio_token" class="flex flex-col items-start gap-2">
                  <span class="font-semibold">{{ t('models.modelDetails.inputAudioCost') }}</span>
                  <span class="text-lg font-light">${{ model.input_cost_per_audio_token.toFixed(4) }}</span>
                </div>
                <div v-if="model?.input_cost_per_token_batches" class="flex flex-col items-start gap-2">
                  <span class="font-semibold">{{ t('models.modelDetails.inputBatchCost') }}</span>
                  <span class="text-lg font-light">${{ model.input_cost_per_token_batches.toFixed(4) }}</span>
                </div>
                <div v-if="model?.output_cost_per_token_batches" class="flex flex-col items-start gap-2">
                  <span class="font-semibold">{{ t('models.modelDetails.outputBatchCost') }}</span>
                  <span class="text-lg font-light">${{ model.output_cost_per_token_batches.toFixed(4) }}</span>
                </div>
                <div v-if="model?.output_cost_per_audio_token" class="flex flex-col items-start gap-2">
                  <span class="font-semibold">{{ t('models.modelDetails.outputAudioCost') }}</span>
                  <span class="text-lg font-light">${{ model.output_cost_per_audio_token.toFixed(4) }}</span>
                </div>
                <div v-if="model?.output_cost_per_reasoning_token" class="flex flex-col items-start gap-2">
                  <span class="font-semibold">{{ t('models.modelDetails.reasoningTokenCost') }}</span>
                  <span class="text-lg font-light">${{ model.output_cost_per_reasoning_token.toFixed(4) }}</span>
                </div>
                <div v-if="model?.output_cost_per_token_above_128k_tokens" class="flex flex-col items-start gap-2">
                  <span class="font-semibold">{{ t('models.modelDetails.outputCostAbove128k') }}</span>
                  <span class="text-lg font-light">${{
                      model.output_cost_per_token_above_128k_tokens.toFixed(4)
                    }}</span>
                </div>
                <div v-if="model?.output_cost_per_token_above_200k_tokens" class="flex flex-col items-start gap-2">
                  <span class="font-semibold">{{ t('models.modelDetails.outputCostAbove200k') }}</span>
                  <span class="text-lg font-light">${{
                      model.output_cost_per_token_above_200k_tokens.toFixed(4)
                    }}</span>
                </div>
                <div v-if="model?.output_cost_per_image" class="flex flex-col items-start gap-2">
                  <span class="font-semibold">{{ t('models.modelDetails.imageCost') }}</span>
                  <span class="text-lg font-light">${{ model.output_cost_per_image.toFixed(4) }}</span>
                </div>
                <div v-if="model?.search_context_cost_per_query" class="flex flex-col items-start gap-2">
                  <span class="font-semibold">{{ t('models.modelDetails.searchContextCost') }}</span>
                  <span class="text-lg font-light">${{ model.search_context_cost_per_query.toFixed(4) }}</span>
                </div>
              </div>
            </div>

            <div v-if="hasRateLimits" class="mb-6">
              <h4 class="text-md font-semibold mb-4">{{ t('models.modelDetails.rateLimits') }}</h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div v-if="model?.tpm" class="flex flex-col items-start gap-2">
                  <span class="font-semibold">{{ t('models.modelDetails.tokensPerMinute') }}</span>
                  <span class="text-lg font-light">{{ formatNumber(model.tpm) }}</span>
                </div>
                <div v-if="model?.rpm" class="flex flex-col items-start gap-2">
                  <span class="font-semibold">{{ t('models.modelDetails.requestsPerMinute') }}</span>
                  <span class="text-lg font-light">{{ formatNumber(model.rpm) }}</span>
                </div>
              </div>
            </div>

            <div class="mb-6">
              <h4 class="text-md font-semibold mb-4">{{ t('models.modelDetails.capabilities') }}</h4>
              <div class="flex flex-wrap gap-2">
                <Badge
                  v-if="model?.supports_system_messages !== null"
                  :value="t('models.modelDetails.supportsSystemMessages')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.supports_response_schema !== null"
                  :value="t('models.modelDetails.supportsResponseSchema')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.supports_vision !== null"
                  :value="t('models.modelDetails.supportsVision')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.supports_function_calling !== null"
                  :value="t('models.modelDetails.supportsFunctionCalling')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.supports_tool_choice !== null"
                  :value="t('models.modelDetails.supportsToolChoice')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.supports_assistant_prefill !== null"
                  :value="t('models.modelDetails.supportsAssistantPrefill')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.supports_prompt_caching !== null"
                  :value="t('models.modelDetails.supportsPromptCaching')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.supports_audio_input !== null"
                  :value="t('models.modelDetails.supportsAudioInput')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.supports_audio_output !== null"
                  :value="t('models.modelDetails.supportsAudioOutput')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.supports_pdf_input !== null"
                  :value="t('models.modelDetails.supportsPdfInput')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.supports_native_streaming !== null"
                  :value="t('models.modelDetails.supportsNativeStreaming')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.supports_web_search !== null"
                  :value="t('models.modelDetails.supportsWebSearch')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.supports_url_context !== null"
                  :value="t('models.modelDetails.supportsUrlContext')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.supports_reasoning !== null"
                  :value="t('models.modelDetails.supportsReasoning')"
                  severity="secondary"
                  class="text-sm"
                />
                <Badge
                  v-if="model?.supports_computer_use !== null"
                  :value="t('models.modelDetails.supportsComputerUse')"
                  severity="secondary"
                  class="text-sm"
                />
              </div>
            </div>

            <div v-if="hasOtherDetails" class="mb-6">
              <h4 class="text-md font-semibold mb-4">{{ t('models.modelDetails.otherDetails') }}</h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div v-if="model?.output_vector_size" class="flex flex-col items-start gap-2">
                  <span class="font-medium text-sm">{{ t('models.modelDetails.outputVectorSize') }}</span>
                  <Tag :value="formatNumber(model.output_vector_size)" severity="secondary"/>
                </div>
                <div v-if="model?.supports_embedding_image_input !== null" class="flex flex-col items-start gap-2">
                  <span class="font-medium text-sm">{{ t('models.modelDetails.supportsEmbeddingImageInput') }}</span>
                  <Tag :value="model?.supports_embedding_image_input ? 'Yes' : 'No'"
                       :severity="model?.supports_embedding_image_input ? 'success' : 'secondary'"/>
                </div>
              </div>
            </div>

            <div v-if="model?.supported_openai_params?.length">
              <h4 class="text-md font-semibold mb-4">{{ t('models.modelDetails.supportedParams') }}</h4>
              <div class="flex flex-wrap gap-2">
                <Badge
                  v-for="param in model.supported_openai_params"
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
import {type ModelDTO} from '@core/sdk/client'

const route = useRoute()
const {t} = useI18n()
const {modelTypes} = useModelsList()

const props = defineProps<{
  model: ModelDTO
}>()

// Local utility function
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

// Check if sections have content
const hasAdvancedPricing = computed(() => {
  if (!model.value) return false
  return !!(model.value.cache_creation_input_token_cost ||
    model.value.cache_read_input_token_cost ||
    model.value.input_cost_per_token_above_128k_tokens ||
    model.value.input_cost_per_token_above_200k_tokens ||
    model.value.input_cost_per_audio_token ||
    model.value.input_cost_per_token_batches ||
    model.value.output_cost_per_token_batches ||
    model.value.output_cost_per_audio_token ||
    model.value.output_cost_per_reasoning_token ||
    model.value.output_cost_per_token_above_128k_tokens ||
    model.value.output_cost_per_token_above_200k_tokens ||
    model.value.output_cost_per_image ||
    model.value.search_context_cost_per_query)
})

const hasRateLimits = computed(() => {
  if (!model.value) return false
  return !!(model.value.tpm || model.value.rpm)
})

const hasOtherDetails = computed(() => {
  if (!model.value) return false
  return model.value.output_vector_size || model.value.supports_embedding_image_input !== null
})
</script>

