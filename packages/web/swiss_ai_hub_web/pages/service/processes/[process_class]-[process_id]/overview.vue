<template>
  <StructuralColumn
    :title="processInstance?.process_config.name"
    close-route="/service/processes"
    :loading="processInstanceIsLoading"
    size="large"
  >
    <div class="flex flex-col gap-12">
      <span class="mb-4 block text-sm text-surface-500 dark:text-surface-400">
        {{ processInstance.process_config.description }}
      </span>
      <Panel
        class="panel pt-5"
      >
        <div class="grid grid-cols-2 gap-4 xl:grid-cols-4">
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('process.overview.name') }}
            </span>
            <Tag
              :value="processInstance.process_config.name"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('process.overview.class') }}
            </span>
            <Tag
              :value="processInstance.process_class"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('process.overview.processId') }}
            </span>
            <Tag
              :value="processInstance.process_id"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('process.overview.status') }}
            </span>
            <Tag
              :value="processInstance.is_online ? t('process.overview.online') : t('process.overview.offline')"
              :severity="processInstance.is_online ? 'success' : 'error' "
            />
          </div>
        </div>
      </Panel>
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
const { processInstance, processInstanceIsLoading } = useProcessInstance()
const { t } = useI18n()
</script>

<style scoped>
.panel :deep(.p-panel-header) {
  padding: 0 !important;
}
</style>
