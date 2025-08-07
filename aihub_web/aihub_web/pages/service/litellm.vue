<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('litellm.title')"
      :loading="pending"
    >
      <div v-if="error" class="mb-4">
        <Message
          severity="error"
          :closable="false"
        >
          {{ t('litellm.error') }}: {{ error }}
        </Message>
      </div>

      <div
        v-if="!pending && !error && models"
        class="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:grid-cols-3"
      >
        <div
          v-for="model in models"
          :key="model.model_name"
          class="flex cursor-pointer flex-col gap-3 rounded-xl border border-surface-200 p-4 hover:bg-surface-100 dark:border-surface-800 hover:dark:bg-surface-800"
        >
          <!-- Model Header -->
          <div class="flex items-center justify-between gap-4">
            <div class="flex items-center justify-start gap-3">
              <div
                class="flex items-center justify-center rounded-full bg-white p-3 dark:bg-surface-900"
              >
                <Icon
                  :name="getModelIcon(model.model_info.mode)"
                  size="1.5em"
                />
              </div>
              <div>
                <h3 class="font-semibold opacity-80">
                  {{ model.model_name }}
                </h3>
                <p class="text-xs font-light opacity-70">
                  {{ model.model_info.key }}
                </p>
              </div>
            </div>
            <div>
              <Tag
                :severity="getModeSeverity(model.model_info.mode)"
                :value="model.model_info.mode"
              />
            </div>
          </div>

          <!-- Model Metrics -->
          <div class="space-y-2">
            <div v-if="model.model_info.max_tokens" class="flex justify-between text-sm">
              <span class="opacity-70">{{ t('litellm.maxTokens') }}:</span>
              <Badge :value="formatNumber(model.model_info.max_tokens)" />
            </div>
            <div v-if="model.model_info.max_input_tokens" class="flex justify-between text-sm">
              <span class="opacity-70">{{ t('litellm.maxInput') }}:</span>
              <Badge :value="formatNumber(model.model_info.max_input_tokens)" />
            </div>
            <div v-if="model.model_info.max_output_tokens" class="flex justify-between text-sm">
              <span class="opacity-70">{{ t('litellm.maxOutput') }}:</span>
              <Badge :value="formatNumber(model.model_info.max_output_tokens)" />
            </div>
            <div v-if="model.model_info.output_vector_size" class="flex justify-between text-sm">
              <span class="opacity-70">{{ t('litellm.vectorSize') }}:</span>
              <Badge :value="model.model_info.output_vector_size" />
            </div>
          </div>

          <!-- Cost Information -->
          <div
            v-if="model.model_info.input_cost_per_token || model.model_info.output_cost_per_token"
            class="space-y-2"
          >
            <Divider />
            <div class="text-xs opacity-70">
              {{ t('litellm.pricing') }}
            </div>
            <div class="space-y-1 text-xs">
              <div v-if="model.model_info.input_cost_per_token" class="flex justify-between">
                <span class="opacity-70">{{ t('litellm.inputCost') }}:</span>
                <span class="font-mono">${{ formatCost(model.model_info.input_cost_per_token) }}</span>
              </div>
              <div v-if="model.model_info.output_cost_per_token" class="flex justify-between">
                <span class="opacity-70">{{ t('litellm.outputCost') }}:</span>
                <span class="font-mono">${{ formatCost(model.model_info.output_cost_per_token) }}</span>
              </div>
              <div v-if="model.model_info.cache_read_input_token_cost" class="flex justify-between">
                <span class="opacity-70">{{ t('litellm.cacheReadCost') }}:</span>
                <span class="font-mono">${{ formatCost(model.model_info.cache_read_input_token_cost) }}</span>
              </div>
            </div>
          </div>

          <!-- Rate Limits -->
          <div v-if="model.model_info.tpm || model.model_info.rpm" class="space-y-2">
            <Divider />
            <div class="text-xs opacity-70">
              {{ t('litellm.rateLimits') }}
            </div>
            <div class="flex gap-2">
              <Badge
                v-if="model.model_info.tpm"
                :value="`${formatNumber(model.model_info.tpm)} TPM`"
                severity="secondary"
              />
              <Badge
                v-if="model.model_info.rpm"
                :value="`${formatNumber(model.model_info.rpm)} RPM`"
                severity="secondary"
              />
            </div>
          </div>

          <!-- API Details -->
          <div v-if="model.litellm_params.api_base || model.litellm_params.api_version" class="space-y-2">
            <Divider />
            <div class="text-xs opacity-70">
              {{ t('litellm.apiDetails') }}
            </div>
            <div class="space-y-1 text-xs">
              <div v-if="model.litellm_params.api_base" class="flex justify-between">
                <span class="opacity-70">{{ t('litellm.apiBase') }}:</span>
                <span class="break-all font-mono text-right">{{ model.litellm_params.api_base }}</span>
              </div>
              <div v-if="model.litellm_params.api_version" class="flex justify-between">
                <span class="opacity-70">{{ t('litellm.apiVersion') }}:</span>
                <span class="font-mono">{{ model.litellm_params.api_version }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </StructuralColumn>
  </StructuralScreen>
</template>

<script setup lang="ts">
interface LiteLLMParams {
  api_base?: string
  api_version?: string
  model: string
}

interface ModelInfo {
  mode: string
  key: string
  max_tokens?: number
  max_input_tokens?: number
  max_output_tokens?: number
  input_cost_per_token?: number
  cache_read_input_token_cost?: number
  output_cost_per_token?: number
  input_cost_per_token_batches?: number
  output_cost_per_token_batches?: number
  output_vector_size?: number
  input_cost_per_audio_token?: number
  output_cost_per_reasoning_token?: number
  tpm?: number
  rpm?: number
}

interface LLMModel {
  model_name: string
  litellm_params: LiteLLMParams
  model_info: ModelInfo
}

definePageMeta({
  layout: 'default',
})

const { t } = useI18n()

const {data: models, pending, error} = await useFetch<LLMModel[]>('/api/v1/litellm/model_info')

function getModelIcon(mode: string): string {
  switch (mode) {
    case 'chat':
      return 'material-symbols:chat-bubble-outline'
    case 'embedding':
      return 'material-symbols:data-object'
    default:
      return 'material-symbols:model-training'
  }
}

function getModeSeverity(mode: string): string {
  switch (mode) {
    case 'chat':
      return 'info'
    case 'embedding':
      return 'success'
    default:
      return 'secondary'
  }
}

function formatNumber(num: number): string {
  return new Intl.NumberFormat().format(num)
}

function formatCost(cost: number): string {
  return cost.toExponential(2)
}
</script>
