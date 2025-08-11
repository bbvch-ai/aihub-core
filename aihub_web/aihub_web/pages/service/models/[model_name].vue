<template>
  <StructuralColumn
    :title="t('models.modelDetails.overview')"
    close-route="/service/models"
  >
    <div class="flex flex-col gap-12">
      <span class="mb-4 block text-sm text-surface-500 dark:text-surface-400">
        {{ selectedModel?.model_info?.description || t('models.modelDetails.no_description') }}
      </span>
      <Panel
        class="panel pt-5"
      >
        <div class="grid grid-cols-2 gap-4 xl:grid-cols-4">
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.overview.name') }}
            </span>
            <Tag
              :value="selectedModel?.model_name"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.overview.mode') }}
            </span>
            <Tag
              :value="selectedModel?.model_info?.mode"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.overview.provider') }}
            </span>
            <Tag
              :value="selectedModel?.model_info?.provider"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.overview.status') }}
            </span>
            <Tag
              :value="selectedModel?.model_info?.status || 'available'"
              :severity="(selectedModel?.model_info?.status || 'available') === 'available' ? 'success' : 'error'"
            />
          </div>
        </div>
      </Panel>
      <Panel class="panel pt-5">
        <div class="grid grid-cols-2 gap-4 xl:grid-cols-4">
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.modelGroup') }}
            </span>
            <Tag
              :value="model?.model_name"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.mode') }}
            </span>
            <Tag
              :severity="getModeSeverity(model?.model_info?.mode)"
              :value="model?.model_info?.mode"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.provider') }}
            </span>
            <Tag
              :value="model_features.name"
              :severity="model_features.severity"
            />
          </div>
          <div v-if="model?.model_info?.id" class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.modelId') }}
            </span>
            <Tag
              :value="model?.model_info?.id"
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
              :value="model?.model_info?.max_input_tokens ? formatNumber(model.model_info.max_input_tokens) : t('models.modelDetails.notSpecified')"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.maxOutputTokens') }}
            </span>
            <Tag
              :value="model?.model_info?.max_output_tokens ? formatNumber(model.model_info.max_output_tokens) : t('models.modelDetails.notSpecified')"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.inputCostPer1M') }}
            </span>
            <Tag
              :value="model?.model_info?.input_cost_per_token ? formatCostPer1M(model.model_info.input_cost_per_token) : t('models.modelDetails.notSpecified')"
              severity="success"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('models.modelDetails.outputCostPer1M') }}
            </span>
            <Tag
              :value="model?.model_info?.output_cost_per_token ? formatCostPer1M(model.model_info.output_cost_per_token) : t('models.modelDetails.notSpecified')"
              severity="success"
            />
          </div>
        </div>
      </Panel>

      <Panel v-if="model_features.length" class="panel pt-5">
        <template #header>
          <h3 class="text-lg font-semibold">{{ t('models.modelDetails.capabilities') }}</h3>
        </template>
        <div class="flex flex-wrap gap-2">
          <Badge
            v-for="feature in model_features"
            :key="feature.name"
            :value="feature.name"
            :severity="feature.severity"
            class="text-sm"
          />
        </div>
      </Panel>

      <Panel v-if="model?.model_info?.supported_openai_params?.length" class="panel pt-5">
        <template #header>
          <h3 class="text-lg font-semibold">{{ t('models.modelDetails.supportedParams') }}</h3>
        </template>
        <div class="flex flex-wrap gap-2">
          <Badge
            v-for="param in model?.model_info?.supported_openai_params"
            :key="param"
            :value="param"
            severity="info"
            class="text-sm"
          />
        </div>
      </Panel>
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
const route = useRoute()
const {t} = useI18n()
const {modelTypes, modelsAreLoading} = useModelsList()

const props = defineProps<{
  model: any
}>()

const {
  getModeSeverity,
  formatCostPer1M,
  formatNumber,
} = useModelsUtils()

const model_features = [
  {
    name: "Test",
    severity: "secondary"
  }
]

const selectedModel = computed(() => {
  if (!modelTypes.value) return null

  const modelName = decodeURIComponent(route.params?.model_name as string)

  for (const modelType of modelTypes.value) {
    const model = modelType.models.find((m: any) => m?.model_name === modelName)
    if (model) return model
  }

  return null
})
</script>

<style scoped>
.panel :deep(.p-panel-header) {
  padding: 0 !important;
}
</style>
