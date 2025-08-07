<template>
  <div class="p-6">
    <h1 class="mb-4 text-2xl font-bold">LiteLLM Service</h1>
    <p class="mb-6 text-gray-600 dark:text-gray-400">Manage and interact with LiteLLM models</p>

    <div v-if="pending" class="flex items-center justify-center p-8">
      <div class="text-gray-500 dark:text-gray-400">Loading models...</div>
    </div>

    <div v-else-if="error"
         class="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20">
      <p class="text-red-800 dark:text-red-400">Error: {{ error }}</p>
    </div>

    <div v-if="!pending && !error && models" class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="model in models"
        :key="model.model_name"
        class="rounded-lg border border-gray-200 bg-gray-50 p-6 shadow-sm transition-shadow hover:shadow-md dark:border-surface-600 dark:bg-surface-800"
      >
        <!-- Model Header -->
        <div class="mb-4 flex items-start justify-between">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ model.model_name }}</h3>
          <span
            :class="getModeClass(model.model_info.mode)"
            class="rounded-full px-3 py-1 text-xs font-medium"
          >
            {{ model.model_info.mode }}
          </span>
        </div>

        <!-- Key Metrics -->
        <div class="mb-4 space-y-2">
          <div v-if="model.model_info.max_tokens" class="flex justify-between text-sm">
            <span class="text-gray-600 dark:text-gray-100">Max Tokens:</span>
            <span class="font-medium dark:text-white">{{ formatNumber(model.model_info.max_tokens) }}</span>
          </div>
          <div v-if="model.model_info.max_input_tokens" class="flex justify-between text-sm">
            <span class="text-gray-600 dark:text-gray-100">Max Input:</span>
            <span class="font-medium dark:text-white">{{ formatNumber(model.model_info.max_input_tokens) }}</span>
          </div>
          <div v-if="model.model_info.max_output_tokens" class="flex justify-between text-sm">
            <span class="text-gray-600 dark:text-gray-100">Max Output:</span>
            <span class="font-medium dark:text-white">{{ formatNumber(model.model_info.max_output_tokens) }}</span>
          </div>
        </div>

        <!-- Cost Information -->
        <div v-if="model.model_info.input_cost_per_token || model.model_info.output_cost_per_token" class="mb-4">
          <h4 class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-100">Pricing (per token)</h4>
          <div class="space-y-1 text-xs text-gray-600 dark:text-gray-100">
            <div v-if="model.model_info.input_cost_per_token" class="flex justify-between">
              <span>Input:</span>
              <span>${{ formatCost(model.model_info.input_cost_per_token) }}</span>
            </div>
            <div v-if="model.model_info.output_cost_per_token" class="flex justify-between">
              <span>Output:</span>
              <span>${{ formatCost(model.model_info.output_cost_per_token) }}</span>
            </div>
            <div v-if="model.model_info.cache_read_input_token_cost" class="flex justify-between">
              <span>Cache Read:</span>
              <span>${{ formatCost(model.model_info.cache_read_input_token_cost) }}</span>
            </div>
          </div>
        </div>

        <!-- Additional Model Info -->
        <div v-if="model.model_info.output_vector_size" class="mb-4">
          <div class="flex justify-between text-sm">
            <span class="text-gray-600 dark:text-gray-100">Vector Size:</span>
            <span class="font-medium dark:text-white">{{ model.model_info.output_vector_size }}</span>
          </div>
        </div>

        <!-- Rate Limits -->
        <div v-if="model.model_info.tpm || model.model_info.rpm" class="mb-4">
          <h4 class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-100">Rate Limits</h4>
          <div class="space-y-1 text-xs text-gray-600 dark:text-gray-100">
            <div v-if="model.model_info.tpm" class="flex justify-between">
              <span>Tokens/min:</span>
              <span>{{ formatNumber(model.model_info.tpm) }}</span>
            </div>
            <div v-if="model.model_info.rpm" class="flex justify-between">
              <span>Requests/min:</span>
              <span>{{ formatNumber(model.model_info.rpm) }}</span>
            </div>
          </div>
        </div>

        <!-- API Details (collapsed by default) -->
        <details class="mt-4">
          <summary
            class="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900 dark:text-gray-100 dark:hover:text-white">
            API Details
          </summary>
          <div class="mt-2 space-y-1 text-xs text-gray-600 dark:text-gray-100">
            <div class="flex justify-between">
              <span>Model Key:</span>
              <span class="font-mono">{{ model.model_info.key }}</span>
            </div>
            <div v-if="model.litellm_params.api_base" class="flex justify-between">
              <span>API Base:</span>
              <span class="break-all font-mono">{{ model.litellm_params.api_base }}</span>
            </div>
            <div v-if="model.litellm_params.api_version" class="flex justify-between">
              <span>API Version:</span>
              <span class="font-mono">{{ model.litellm_params.api_version }}</span>
            </div>
          </div>
        </details>
      </div>
    </div>
  </div>
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

const {data: models, pending, error} = await useFetch<LLMModel[]>('/api/v1/litellm/model_info')

function getModeClass(mode: string): string {
  switch (mode) {
    case 'chat':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
    case 'embedding':
      return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-800/30 dark:text-gray-400'
  }
}

function formatNumber(num: number): string {
  return new Intl.NumberFormat().format(num)
}

function formatCost(cost: number): string {
  return cost.toExponential(2)
}
</script>
