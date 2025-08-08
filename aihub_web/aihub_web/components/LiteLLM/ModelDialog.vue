<template>
  <Dialog
    :visible="visible"
    modal
    :header="model?.model_name || ''"
    style="width: 1000px"
    :breakpoints="{ '960px': '90vw' }"
    class="model-details-dialog"
    @update:visible="$emit('update:visible', $event)"
  >
    <div v-if="model" class="space-y-6">
      <div>
        <h3 class="text-lg font-semibold mb-4">{{ t('litellm.modelDetails.overview') }}</h3>
        <div class="grid grid-cols-2 gap-4 mb-4">
          <div>
            <p class="font-medium mb-1">{{ t('litellm.modelDetails.modelGroup') }}:</p>
            <p>{{ model.model_name }}</p>
          </div>
          <div>
            <p class="font-medium mb-1">{{ t('litellm.modelDetails.mode') }}:</p>
            <Tag
              :severity="getModeSeverity(model.model_info.mode)"
              :value="model.model_info.mode"
            />
          </div>
          <div>
            <p class="font-medium mb-1">{{ t('litellm.modelDetails.provider') }}:</p>
            <div class="flex flex-wrap gap-1 mt-1">
              <Tag
                :value="getProvider(model)"
                :severity="getProviderSeverity(getProvider(model))"
              />
            </div>
          </div>
          <div v-if="model.model_info.id">
            <p class="font-medium mb-1">{{ t('litellm.modelDetails.modelId') }}:</p>
            <p class="text-xs font-mono break-all">{{ model.model_info.id }}</p>
          </div>
        </div>
      </div>

      <div>
        <h3 class="text-lg font-semibold mb-4">{{ t('litellm.modelDetails.tokenCost') }}</h3>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <p class="font-medium mb-1">{{ t('litellm.modelDetails.maxInputTokens') }}:</p>
            <p>{{
                model.model_info.max_input_tokens ? formatNumber(model.model_info.max_input_tokens) :
                  t('litellm.modelDetails.notSpecified')
              }}</p>
          </div>
          <div>
            <p class="font-medium mb-1">{{ t('litellm.modelDetails.maxOutputTokens') }}:</p>
            <p>{{
                model.model_info.max_output_tokens ? formatNumber(model.model_info.max_output_tokens)
                  : t('litellm.modelDetails.notSpecified')
              }}</p>
          </div>
          <div>
            <p class="font-medium mb-1">{{ t('litellm.modelDetails.inputCostPer1M') }}:</p>
            <p>{{
                model.model_info.input_cost_per_token ?
                  formatCostPer1M(model.model_info.input_cost_per_token) :
                  t('litellm.modelDetails.notSpecified')
              }}</p>
          </div>
          <div>
            <p class="font-medium mb-1">{{ t('litellm.modelDetails.outputCostPer1M') }}:</p>
            <p>{{
                model.model_info.output_cost_per_token ?
                  formatCostPer1M(model.model_info.output_cost_per_token) :
                  t('litellm.modelDetails.notSpecified')
              }}</p>
          </div>
          <div v-if="model.model_info.cache_read_input_token_cost">
            <p class="font-medium mb-1">{{ t('litellm.modelDetails.cacheReadCostPer1M') }}:</p>
            <p>{{ formatCostPer1M(model.model_info.cache_read_input_token_cost) }}</p>
          </div>
          <div v-if="model.model_info.output_vector_size">
            <p class="font-medium mb-1">{{ t('litellm.modelDetails.vectorSize') }}:</p>
            <p>{{ model.model_info.output_vector_size }}D</p>
          </div>
        </div>
      </div>

      <div v-if="model.model_info.tpm || model.model_info.rpm">
        <h3 class="text-lg font-semibold mb-4">{{ t('litellm.modelDetails.rateLimits') }}</h3>
        <div class="grid grid-cols-2 gap-4">
          <div v-if="model.model_info.tpm">
            <p class="font-medium mb-1">{{ t('litellm.modelDetails.tokensPerMinute') }}:</p>
            <p>{{ formatNumber(model.model_info.tpm) }}</p>
          </div>
          <div v-if="model.model_info.rpm">
            <p class="font-medium mb-1">{{ t('litellm.modelDetails.requestsPerMinute') }}:</p>
            <p>{{ formatNumber(model.model_info.rpm) }}</p>
          </div>
        </div>
      </div>

      <div>
        <h3 class="text-lg font-semibold mb-4">{{ t('litellm.modelDetails.capabilities') }}</h3>
        <div class="flex flex-wrap gap-2">
          <Badge
            v-for="feature in getModelFeatures(model)"
            :key="feature.name"
            :value="feature.name"
            :severity="feature.severity"
            class="text-sm"
          />
          <p
            v-if="!getModelFeatures(model).length"
            class="text-gray-500"
          >
            {{ t('litellm.modelDetails.noCapabilities') }}
          </p>
        </div>
      </div>

      <div>
        <h3 class="text-lg font-semibold mb-4">{{ t('litellm.modelDetails.supportedParams') }}</h3>
        <div class="flex flex-wrap gap-2">
          <Badge
            v-for="param in model.model_info.supported_openai_params || []"
            :key="param"
            :value="param"
            severity="success"
            class="text-sm"
          />
          <p
            v-if="!model.model_info.supported_openai_params?.length"
            class="text-gray-500"
          >
            {{ t('litellm.modelDetails.notAvailable') }}
          </p>
        </div>
      </div>

      <div>
        <h3 class="text-lg font-semibold mb-4">{{ t('litellm.modelDetails.usageExample') }}</h3>
        <pre class="bg-gray-100 dark:bg-gray-800 p-4 rounded text-sm overflow-x-auto"><code>{{
            getUsageExample(model)
          }}</code></pre>
      </div>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
const props = defineProps<{
  visible: boolean
  model: any
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

const { t } = useI18n()
const { 
  getProvider, 
  getProviderSeverity, 
  getModeSeverity, 
  formatCostPer1M, 
  getModelFeatures,
  formatNumber,
  getUsageExample
} = useLiteLLMUtils()
</script>