<template>
  <StructuralColumn
    :title="selectedModel?.model_name"
    close-route="/service/models"
    :loading="modelsAreLoading"
    size="large"
  >
    <div class="flex flex-col gap-12">
      <span class="mb-4 block text-sm text-surface-500 dark:text-surface-400">
        {{ selectedModel?.model_info?.description || t('models.no_description') }}
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
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
const route = useRoute()
const {t} = useI18n()
const {modelTypes, modelsAreLoading} = useModelsList()


const selectedModel = computed(() => {
  if (!modelTypes.value) return null

  const modelName = decodeURIComponent(route.params.model_name as string)

  for (const modelType of modelTypes.value) {
    const model = modelType.models.find((m: any) => m.model_name === modelName)
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
