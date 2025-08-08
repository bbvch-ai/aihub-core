<template>
  <DataTable
    :value="models"
    table-style="min-width: 50rem"
    :paginator="true"
    :rows="3"
    :rows-per-page-options="[3, 5, 10]"
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
const {
  getProvider,
  getProviderSeverity,
  getModeSeverity,
  formatTokenLimits,
  formatCostPer1M,
  getModelFeatures,
  formatNumber,
  copyToClipboard
} = useModelsUtils()
</script>
