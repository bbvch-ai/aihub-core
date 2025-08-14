<template>
  <DataTable
    :value="models"
    table-style="min-width: 50rem"
    :paginator="true"
    :rows="3"
    :rows-per-page-options="[3, 5, 10]"
    paginator-template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
    :current-page-report-template="t('models.table.pageReport')"
    responsive-layout="scroll"
  >
    <Column
      field="model_name"
      :header="t('models.table.modelName')"
      :sortable="true"
      style="min-width: 200px"
    >
      <template #body="{ data }">
        <div class="space-y-1">
          <div class="flex items-center space-x-2">
            <p class="font-medium text-sm text-gray-900 dark:text-gray-100">{{ data.model_name }}</p>
            <Button
              v-tooltip="t('models.table.copyModelName')"
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
      :header="t('models.table.provider')"
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
      :header="t('models.table.mode')"
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
      :header="t('models.table.tokens')"
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
      :header="t('models.table.costPer1M')"
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
      :header="t('models.table.features')"
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
      :header="t('models.table.rateLimits')"
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
      :header="t('models.table.details')"
      style="min-width: 100px"
    >
      <template #body="{ data }">
        <Button
          icon="pi pi-info-circle"
          :label="t('models.table.detailsButton')"
          severity="info"
          outlined
          size="small"
          @click="$emit('showDetails', data)"
        />
      </template>
    </Column>
  </DataTable>
</template>

<script setup lang="ts">

const props = defineProps<{
  models: any[]
}>()

const emit = defineEmits<{
  showDetails: [model: any]
}>()

const {t} = useI18n()
const toast = useToast()

// Local utility functions
const formatNumber = (num: number): string => {
  return new Intl.NumberFormat().format(num)
}

const getModeSeverity = (mode: string): string => {
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

const formatTokenLimits = (model: any): string => {
  const input = model?.model_info?.max_input_tokens
  const output = model?.model_info?.max_output_tokens

  if (input && output) {
    return `${formatNumber(input)} / ${formatNumber(output)}`
  } else if (input) {
    return `${formatNumber(input)} / -`
  } else if (output) {
    return `- / ${formatNumber(output)}`
  }
  return '- / -'
}

const copyToClipboard = async (text: string) => {
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

// These functions seem to be missing from the original utils, adding placeholder implementations
const getProvider = (data: any): string => {
  // Extract provider from model name or use a default
  return data.model_name?.split('/')[0] || 'Unknown'
}

const getProviderSeverity = (provider: string): string => {
  // Simple provider-based severity mapping
  switch (provider.toLowerCase()) {
    case 'openai':
      return 'success'
    case 'anthropic':
      return 'info'
    case 'google':
      return 'warn'
    default:
      return 'secondary'
  }
}

const formatCostPer1M = (costPerToken: number | null | undefined): string => {
  if (costPerToken === null || costPerToken === undefined) {
    return '-'
  }
  const costPer1M = costPerToken * 1000000
  return `$${costPer1M.toFixed(2)}`
}

const getModelFeatures = (data: any): Array<{name: string, severity: string}> => {
  const features: Array<{name: string, severity: string}> = []
  
  if (data.model_info?.supports_vision) {
    features.push({ name: 'Vision', severity: 'info' })
  }
  if (data.model_info?.supports_function_calling) {
    features.push({ name: 'Functions', severity: 'success' })
  }
  if (data.model_info?.supports_streaming) {
    features.push({ name: 'Streaming', severity: 'help' })
  }
  
  return features
}
</script>
