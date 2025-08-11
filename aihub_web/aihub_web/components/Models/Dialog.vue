<template>
  <StructuralColumn
    :title="t('knowledge.documents.title')"
    close-route="/service/models"
  >
    <div v-if="model" class="flex flex-col gap-12">
      <span class="mb-4 block text-sm text-surface-500 dark:text-surface-400">
        {{ t('models.modelDetails.overview') }}
      </span>

      <Panel class="panel pt-5">
        <div class="grid grid-cols-2 gap-4 xl:grid-cols-4">
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.modelGroup') }}
            </span>
            <Tag
              :value="model.model_name"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.mode') }}
            </span>
            <Tag
              :severity="getModeSeverity(model.model_info.mode)"
              :value="model.model_info.mode"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.provider') }}
            </span>
            <Tag
              :value="getProvider(model)"
              :severity="getProviderSeverity(getProvider(model))"
            />
          </div>
          <div v-if="model.model_info.id" class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.modelId') }}
            </span>
            <Tag
              :value="model.model_info.id"
              severity="secondary"
            />
          </div>
        </div>
      </Panel>

      <Panel class="panel pt-5">
        <template #header>
          <h3 class="text-lg font-semibold">{{ t('models.modelDetails.tokenCost') }}</h3>
        </template>
        <div class="grid grid-cols-2 gap-4 xl:grid-cols-3">
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.maxInputTokens') }}
            </span>
            <Tag
              :value="model.model_info.max_input_tokens ? formatNumber(model.model_info.max_input_tokens) : t('models.modelDetails.notSpecified')"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.maxOutputTokens') }}
            </span>
            <Tag
              :value="model.model_info.max_output_tokens ? formatNumber(model.model_info.max_output_tokens) : t('models.modelDetails.notSpecified')"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.inputCostPer1M') }}
            </span>
            <Tag
              :value="model.model_info.input_cost_per_token ? formatCostPer1M(model.model_info.input_cost_per_token) : t('models.modelDetails.notSpecified')"
              severity="success"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.outputCostPer1M') }}
            </span>
            <Tag
              :value="model.model_info.output_cost_per_token ? formatCostPer1M(model.model_info.output_cost_per_token) : t('models.modelDetails.notSpecified')"
              severity="success"
            />
          </div>
        </div>
      </Panel>

      <Panel v-if="getModelFeatures(model).length" class="panel pt-5">
        <template #header>
          <h3 class="text-lg font-semibold">{{ t('models.modelDetails.capabilities') }}</h3>
        </template>
        <div class="flex flex-wrap gap-2">
          <Badge
            v-for="feature in getModelFeatures(model)"
            :key="feature.name"
            :value="feature.name"
            :severity="feature.severity"
            class="text-sm"
          />
        </div>
      </Panel>

      <Panel v-if="model.model_info.supported_openai_params?.length" class="panel pt-5">
        <template #header>
          <h3 class="text-lg font-semibold">{{ t('models.modelDetails.supportedParams') }}</h3>
        </template>
        <div class="flex flex-wrap gap-2">
          <Badge
            v-for="param in model.model_info.supported_openai_params"
            :key="param"
            :value="param"
            severity="info"
            class="text-sm"
          />
        </div>
      </Panel>

      <Panel class="panel pt-5">
        <template #header>
          <h3 class="text-lg font-semibold">{{ t('models.modelDetails.usageExample') }}</h3>
        </template>
        <pre class="bg-gray-100 dark:bg-gray-800 p-4 rounded text-sm overflow-x-auto"><code>{{
            getUsageExample(model)
          }}</code></pre>
      </Panel>
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
const props = defineProps<{
  model: any
}>()

const {t} = useI18n()
const {
  getProvider,
  getProviderSeverity,
  getModeSeverity,
  formatCostPer1M,
  getModelFeatures,
  formatNumber,
  getUsageExample
} = useModelsUtils()
</script>

<style scoped>
.panel :deep(.p-panel-header) {
  padding: 0 !important;
}
</style>
