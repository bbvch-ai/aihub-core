<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('litellm.title')"
      :loading="pending"
      class="w-1/2 pr-2"
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
          :rows="5"
          :rows-per-page-options="[5, 15, 25]"
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
                  <p class="font-medium text-sm text-gray-900 dark:text-gray-100">{{ data.model_name }}</p>
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
                  <p class="text-xs text-gray-600 dark:text-gray-400">{{ getProvider(data) }}</p>
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
                <p class="text-xs text-gray-900 dark:text-gray-100">
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
                <p class="text-xs font-medium text-gray-900 dark:text-gray-100">
                  {{ formatCostPer1M(data.model_info.input_cost_per_token) }}
                </p>
                <p class="text-xs text-gray-600 dark:text-gray-400">
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
                  class="text-xs text-gray-600 dark:text-gray-400"
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
                  class="text-xs text-gray-600 dark:text-gray-400"
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


      <Dialog
        v-model:visible="modelDialogVisible"
        modal
        :header="selectedModel?.model_name || ''"
        style="width: 1000px"
        :breakpoints="{ '960px': '90vw' }"
        class="model-details-dialog"
      >
        <div v-if="selectedModel" class="space-y-6">
          <div>
            <h3 class="text-lg font-semibold mb-4">{{ t('litellm.modelDetails.overview') }}</h3>
            <div class="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.modelGroup') }}:</p>
                <p>{{ selectedModel.model_name }}</p>
              </div>
              <div>
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.mode') }}:</p>
                <Tag
                  :severity="getModeSeverity(selectedModel.model_info.mode)"
                  :value="selectedModel.model_info.mode"
                />
              </div>
              <div>
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.provider') }}:</p>
                <div class="flex flex-wrap gap-1 mt-1">
                  <Tag
                    :value="getProvider(selectedModel)"
                    :severity="getProviderSeverity(getProvider(selectedModel))"
                  />
                </div>
              </div>
              <div v-if="selectedModel.model_info.id">
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.modelId') }}:</p>
                <p class="text-xs font-mono break-all">{{ selectedModel.model_info.id }}</p>
              </div>
            </div>
          </div>

          <div>
            <h3 class="text-lg font-semibold mb-4">{{ t('litellm.modelDetails.tokenCost') }}</h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.maxInputTokens') }}:</p>
                <p>{{
                    selectedModel.model_info.max_input_tokens ? formatNumber(selectedModel.model_info.max_input_tokens) :
                      t('litellm.modelDetails.notSpecified')
                  }}</p>
              </div>
              <div>
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.maxOutputTokens') }}:</p>
                <p>{{
                    selectedModel.model_info.max_output_tokens ? formatNumber(selectedModel.model_info.max_output_tokens)
                      : t('litellm.modelDetails.notSpecified')
                  }}</p>
              </div>
              <div>
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.inputCostPer1M') }}:</p>
                <p>{{
                    selectedModel.model_info.input_cost_per_token ?
                      formatCostPer1M(selectedModel.model_info.input_cost_per_token) :
                      t('litellm.modelDetails.notSpecified')
                  }}</p>
              </div>
              <div>
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.outputCostPer1M') }}:</p>
                <p>{{
                    selectedModel.model_info.output_cost_per_token ?
                      formatCostPer1M(selectedModel.model_info.output_cost_per_token) :
                      t('litellm.modelDetails.notSpecified')
                  }}</p>
              </div>
              <div v-if="selectedModel.model_info.cache_read_input_token_cost">
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.cacheReadCostPer1M') }}:</p>
                <p>{{ formatCostPer1M(selectedModel.model_info.cache_read_input_token_cost) }}</p>
              </div>
              <div v-if="selectedModel.model_info.output_vector_size">
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.vectorSize') }}:</p>
                <p>{{ selectedModel.model_info.output_vector_size }}D</p>
              </div>
            </div>
          </div>

          <div v-if="selectedModel.model_info.tpm || selectedModel.model_info.rpm">
            <h3 class="text-lg font-semibold mb-4">{{ t('litellm.modelDetails.rateLimits') }}</h3>
            <div class="grid grid-cols-2 gap-4">
              <div v-if="selectedModel.model_info.tpm">
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.tokensPerMinute') }}:</p>
                <p>{{ formatNumber(selectedModel.model_info.tpm) }}</p>
              </div>
              <div v-if="selectedModel.model_info.rpm">
                <p class="font-medium mb-1">{{ t('litellm.modelDetails.requestsPerMinute') }}:</p>
                <p>{{ formatNumber(selectedModel.model_info.rpm) }}</p>
              </div>
            </div>
          </div>

          <div>
            <h3 class="text-lg font-semibold mb-4">{{ t('litellm.modelDetails.capabilities') }}</h3>
            <div class="flex flex-wrap gap-2">
              <Badge
                v-for="feature in getModelFeatures(selectedModel)"
                :key="feature.name"
                :value="feature.name"
                :severity="feature.severity"
                class="text-sm"
              />
              <p
                v-if="!getModelFeatures(selectedModel).length"
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
                v-for="param in selectedModel.model_info.supported_openai_params || []"
                :key="param"
                :value="param"
                severity="success"
                class="text-sm"
              />
              <p
                v-if="!selectedModel.model_info.supported_openai_params?.length"
                class="text-gray-500"
              >
                {{ t('litellm.modelDetails.notAvailable') }}
              </p>
            </div>
          </div>

          <div>
            <h3 class="text-lg font-semibold mb-4">{{ t('litellm.modelDetails.usageExample') }}</h3>
            <pre class="bg-gray-100 dark:bg-gray-800 p-4 rounded text-sm overflow-x-auto"><code>{{
                getUsageExample(selectedModel)
              }}</code></pre>
          </div>
        </div>
      </Dialog>
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
  id?: string
  db_model?: boolean
  base_model?: string
  mode: string
  key: string
  max_tokens?: number
  max_input_tokens?: number
  max_output_tokens?: number
  input_cost_per_token?: number
  output_cost_per_token?: number
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
  output_vector_size?: number
  litellm_provider?: string
  custom_tokenizer?: CustomTokenizer
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
  tpm?: number
  rpm?: number
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

const modelDialogVisible = ref(false)
const selectedModel = ref<LLMModel | null>(null)

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
  selectedModel.value = model
  modelDialogVisible.value = true
}

function getUsageExample(model: LLMModel): string {
  const isImageGeneration = model.model_info.mode === 'image_generation'
  const isEmbedding = model.model_info.mode === 'embedding'

  if (isImageGeneration) {
    return `import openai

client = openai.OpenAI(
    api_key="your_api_key",
    base_url="http://0.0.0.0:4000"  # Your LiteLLM Proxy URL
)

response = client.images.generate(
    model="${model.model_name}",
    prompt="A beautiful sunset over mountains",
    size="1024x1024",
    n=1
)

print(response.data[0].url)`
  }

  if (isEmbedding) {
    return `import openai

client = openai.OpenAI(
    api_key="your_api_key",
    base_url="http://0.0.0.0:4000"  # Your LiteLLM Proxy URL
)

response = client.embeddings.create(
    model="${model.model_name}",
    input="Your text to embed here"
)

print(response.data[0].embedding)`
  }

  return `import openai

client = openai.OpenAI(
    api_key="your_api_key",
    base_url="http://0.0.0.0:4000"  # Your LiteLLM Proxy URL
)

response = client.chat.completions.create(
    model="${model.model_name}",
    messages=[
        {
            "role": "user",
            "content": "Hello, how are you?"
        }
    ]
)

print(response.choices[0].message.content)`
}
</script>
