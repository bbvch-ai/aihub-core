<template>
  <StructuralColumn
    :title="agent?.agent_config.name"
    close-route="/admin/agent"
    :loading="agentIsLoading"
    size="large"
  >
    <div class="flex flex-col gap-12">
      <span class="mb-4 block text-sm text-surface-500 dark:text-surface-400">
        {{ agent.agent_config.description }}
      </span>
      <Panel
        class="panel pt-5"
      >
        <div class="grid grid-cols-2 gap-4 xl:grid-cols-4">
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('agent.overview.name') }}
            </span>
            <Tag
              :value="agent.agent_config.name"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('agent.overview.class') }}
            </span>
            <Tag
              :value="agent.agent_class"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('agent.overview.agentId') }}
            </span>
            <Tag
              :value="agent.agent_id"
              severity="secondary"
            />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">
              {{ t('agent.overview.status') }}
            </span>
            <Tag
              :value="agent.is_online ? t('agent.overview.online') : t('agent.overview.offline')"
              :severity="agent.is_online ? 'success' : 'error' "
            />
          </div>
        </div>
      </Panel>
      <EventStatistics
        v-model="timeRange"
        :charts="charts"
      />
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
const { agent, agentIsLoading } = useAgent()
const { t } = useI18n()
const { timeRange, charts } = useBasicEventStatistics()
</script>

<style scoped>
.panel :deep(.p-panel-header) {
  padding: 0 !important;
}
</style>
