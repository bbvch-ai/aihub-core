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

      <div v-if="!pending && !error && models">
        <DataTable
          :value="models"
          table-style="min-width: 50rem"
          :paginator="true"
          :rows="10"
          :rows-per-page-options="[10, 20, 50]"
          paginator-template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
          :current-page-report-template="t('litellm.table.pageReport')"
          responsive-layout="scroll"
        >
          <Column
            field="model_name"
            :header="t('litellm.table.modelName')"
            :sortable="true"
            style="min-width: 200px"
          >
            <template #body="{ data }">
              <div class="space-y-1">
                <div class="flex items-center space-x-2">
                  <p class="font-medium text-sm">{{ data.model_name }}</p>
                  <Button
                    v-tooltip="t('litellm.table.copyModelName')"
                    icon="pi pi-copy"
                    severity="secondary"
                    text
                    size="small"
                    @click="copyToClipboard(data.model_name)"
                  />
                </div>
                <div class="md:hidden">
                  <p class="text-xs opacity-60">{{ getProvider(data) }}</p>
                </div>
              </div>
            </template>
          </Column>

          <Column
            field="provider"
            :header="t('litellm.table.provider')"
            :sortable="true"
            class="hidden md:table-cell"
            style="min-width: 120px"
          >
            <template #body="{ data }">
              <Tag
                :value="getProvider(data)"
                :severity="getProviderSeverity(getProvider(data))"
              />
            </template>
          </Column>

          <Column
            field="model_info.mode"
            :header="t('litellm.table.mode')"
            :sortable="true"
            class="hidden lg:table-cell"
            style="min-width: 150px"
          >
            <template #body="{ data }">
              <Tag
                :severity="getModeSeverity(data.model_info.mode)"
                :value="data.model_info.mode"
              />
            </template>
          </Column>

          <Column
            field="tokens"
            :header="t('litellm.table.tokens')"
            class="hidden lg:table-cell"
            style="min-width: 120px"
          >
            <template #body="{ data }">
              <div class="space-y-1">
                <p class="text-xs">
                  {{ formatTokenLimits(data) }}
                </p>
              </div>
            </template>
          </Column>

          <Column
            field="cost"
            :header="t('litellm.table.costPer1M')"
            style="min-width: 120px"
          >
            <template #body="{ data }">
              <div class="space-y-1">
                <p class="text-xs font-medium">
                  {{ formatCostPer1M(data.model_info.input_cost_per_token) }}
                </p>
                <p class="text-xs opacity-60">
                  {{ formatCostPer1M(data.model_info.output_cost_per_token) }}
                </p>
              </div>
            </template>
          </Column>

          <Column
            field="features"
            :header="t('litellm.table.features')"
            style="min-width: 200px"
          >
            <template #body="{ data }">
              <div class="flex flex-wrap gap-1">
                <Badge
                  v-for="feature in getModelFeatures(data)"
                  :key="feature.name"
                  :value="feature.name"
                  :severity="feature.severity"
                  class="text-xs"
                />
                <span
                  v-if="!getModelFeatures(data).length"
                  class="text-xs opacity-60"
                >
                  -
                </span>
              </div>
            </template>
          </Column>

          <Column
            field="rate_limits"
            :header="t('litellm.table.rateLimits')"
            class="hidden md:table-cell"
            style="min-width: 120px"
          >
            <template #body="{ data }">
              <div class="flex flex-col gap-1">
                <Badge
                  v-if="data.model_info.tpm"
                  :value="`${formatNumber(data.model_info.tpm)} TPM`"
                  severity="secondary"
                  class="text-xs"
                />
                <Badge
                  v-if="data.model_info.rpm"
                  :value="`${formatNumber(data.model_info.rpm)} RPM`"
                  severity="secondary"
                  class="text-xs"
                />
                <span
                  v-if="!data.model_info.tpm && !data.model_info.rpm"
                  class="text-xs opacity-60"
                >
                  -
                </span>
              </div>
            </template>
          </Column>

          <Column
            field="details"
            :header="t('litellm.table.details')"
            style="min-width: 100px"
          >
            <template #body="{ data }">
              <Button
                icon="pi pi-info-circle"
                :label="t('litellm.table.detailsButton')"
                severity="info"
                outlined
                size="small"
                @click="showModelDetails(data)"
              />
            </template>
          </Column>
        </DataTable>
      </div>
    </StructuralColumn>
  </StructuralScreen>
</template>

<script setup lang="ts">
interface CustomTokenizer {
  identifier: string
  revision: string
  auth_token?: string
}

interface LiteLLMParams {
  api_base?: string
  api_version?: string
  use_in_pass_through?: boolean
  use_litellm_proxy?: boolean
  merge_reasoning_content_in_choices?: boolean
  model: string
}

interface ModelInfo {
  // Core identification
  id?: string
  db_model?: boolean
  base_model?: string
  mode: string
  key: string

  // Token limits
  max_tokens?: number
  max_input_tokens?: number
  max_output_tokens?: number

  // Cost information - basic
  input_cost_per_token?: number
  output_cost_per_token?: number

  // Cost information - extended
  cache_creation_input_token_cost?: number
  cache_read_input_token_cost?: number
  input_cost_per_character?: number
  input_cost_per_token_above_128k_tokens?: number
  input_cost_per_token_above_200k_tokens?: number
  input_cost_per_query?: number
  input_cost_per_second?: number
  input_cost_per_audio_token?: number
  input_cost_per_token_batches?: number
  output_cost_per_token_batches?: number
  output_cost_per_audio_token?: number
  output_cost_per_character?: number
  output_cost_per_reasoning_token?: number
  output_cost_per_token_above_128k_tokens?: number
  output_cost_per_character_above_128k_tokens?: number
  output_cost_per_token_above_200k_tokens?: number
  output_cost_per_second?: number
  output_cost_per_image?: number
  citation_cost_per_token?: number
  search_context_cost_per_query?: number

  // Vector information
  output_vector_size?: number

  // Provider and tokenizer
  litellm_provider?: string
  custom_tokenizer?: CustomTokenizer

  // Capability flags
  supports_system_messages?: boolean
  supports_response_schema?: boolean
  supports_vision?: boolean
  supports_function_calling?: boolean
  supports_tool_choice?: boolean
  supports_assistant_prefill?: boolean
  supports_prompt_caching?: boolean
  supports_audio_input?: boolean
  supports_audio_output?: boolean
  supports_pdf_input?: boolean
  supports_embedding_image_input?: boolean
  supports_native_streaming?: boolean
  supports_web_search?: boolean
  supports_url_context?: boolean
  supports_reasoning?: boolean
  supports_computer_use?: boolean

  // Rate limits
  tpm?: number
  rpm?: number

  // Supported parameters
  supported_openai_params?: string[]
}

interface LLMModel {
  model_name: string
  litellm_params: LiteLLMParams
  model_info: ModelInfo
}

definePageMeta({
  layout: 'default',
})

const {t} = useI18n()
const toast = useToast()

const {data: models, pending, error} = await useFetch<LLMModel[]>('/api/v1/litellm/model_info')

function getProvider(model: LLMModel): string {
  if (model.model_info.litellm_provider) {
    return model.model_info.litellm_provider
  }

  const modelName = model.model_name
  if (modelName.includes('azure/')) return 'azure'
  if (modelName.includes('google/') || modelName.includes('gemini')) return 'google'
  if (modelName.includes('openai/')) return 'openai'
  if (modelName.includes('anthropic/')) return 'anthropic'
  if (modelName.includes('local/')) return 'local'
  if (modelName.includes('text-embedding')) return 'openai'
  return 'unknown'
}

function getProviderSeverity(provider: string): string {
  switch (provider) {
    case 'azure':
      return 'info'
    case 'google':
      return 'success'
    case 'openai':
      return 'warn'
    case 'anthropic':
      return 'danger'
    case 'local':
      return 'secondary'
    default:
      return 'secondary'
  }
}

function getModeSeverity(mode: string): string {
  switch (mode) {
    case 'chat':
      return 'info'
    case 'embedding':
      return 'success'
    case 'image_generation':
      return 'warn'
    case 'audio_transcription':
    case 'audio_speech':
      return 'help'
    default:
      return 'secondary'
  }
}

function formatTokenLimits(model: LLMModel): string {
  const input = model.model_info.max_input_tokens
  const output = model.model_info.max_output_tokens

  if (input && output) {
    return `${formatNumber(input)} / ${formatNumber(output)}`
  } else if (input) {
    return `${formatNumber(input)} / -`
  } else if (output) {
    return `- / ${formatNumber(output)}`
  }
  return '- / -'
}

function formatCostPer1M(costPerToken?: number): string {
  if (!costPerToken) return '-'
  const costPer1M = costPerToken * 1000000
  return `$${costPer1M.toFixed(2)}`
}

function getModelFeatures(model: LLMModel): Array<{ name: string, severity: string }> {
  const features: Array<{ name: string, severity: string }> = []

  // Use actual capability flags from the model_info
  if (model.model_info.supports_vision) {
    features.push({name: 'Vision', severity: 'success'})
  }

  if (model.model_info.supports_function_calling) {
    features.push({name: 'Function Calling', severity: 'info'})
  }

  if (model.model_info.supports_web_search) {
    features.push({name: 'Web Search', severity: 'help'})
  }

  if (model.model_info.supports_reasoning) {
    features.push({name: 'Reasoning', severity: 'warn'})
  }

  if (model.model_info.supports_prompt_caching) {
    features.push({name: 'Caching', severity: 'secondary'})
  }

  if (model.model_info.supports_audio_input) {
    features.push({name: 'Audio Input', severity: 'info'})
  }

  if (model.model_info.supports_audio_output) {
    features.push({name: 'Audio Output', severity: 'info'})
  }

  if (model.model_info.supports_pdf_input) {
    features.push({name: 'PDF Input', severity: 'success'})
  }

  if (model.model_info.supports_computer_use) {
    features.push({name: 'Computer Use', severity: 'danger'})
  }

  if (model.model_info.output_vector_size) {
    features.push({name: `${model.model_info.output_vector_size}D`, severity: 'secondary'})
  }

  return features
}

function formatNumber(num: number): string {
  return new Intl.NumberFormat().format(num)
}

async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    toast.add({
      severity: 'success',
      summary: t('litellm.copied'),
      detail: t('litellm.copiedDetail', {text}),
      life: 3000
    })
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: t('litellm.copyFailed'),
      detail: t('litellm.copyFailedDetail'),
      life: 3000
    })
  }
}

function showModelDetails(model: LLMModel) {
  // TODO add a detail page as popup
  toast.add({
    severity: 'info',
    summary: model.model_name,
    detail: `${t('litellm.table.mode')}: ${model.model_info.mode}`,
    life: 5000
  })
}
</script>
