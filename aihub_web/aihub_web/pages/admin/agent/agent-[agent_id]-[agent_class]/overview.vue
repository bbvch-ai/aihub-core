<template>
  <ProgressBar
    v-if="agentIsLoading || !agent"
    mode="indeterminate"
    style="height: 2px"
  />
  <div
    v-else
    class="flex flex-col gap-16 p-3"
  >
    <Panel
      class="panel pt-5"
    >
      <div class="grid grid-cols-2 gap-4 2xl:grid-cols-4">
        <div class="flex items-center gap-2">
          <span class="font-semibold">
            {{ t('agent.overview.name') }}
          </span>
          <Tag
            :value="agent.agent_config.name"
            severity="secondary"
          />
        </div>
        <div class="flex items-center gap-2">
          <span class="font-semibold">
            {{ t('agent.overview.class') }}
          </span>
          <Tag
            :value="agent.agent_class"
            severity="secondary"
          />
        </div>
        <div class="flex items-center gap-2">
          <span class="font-semibold">
            {{ t('agent.overview.agentId') }}
          </span>
          <Tag
            :value="agent.agent_id"
            severity="secondary"
          />
        </div>
        <div class="flex items-center gap-2">
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
</template>

<script setup lang="ts">
const { agent, agentIsLoading } = useAgent()
const { t } = useI18n()
const { timeRange, charts } = useBasicEventStatistics()
</script>

<style scoped>
::v-deep(.panel) {
  .p-panel-header {
    padding: 0 !important;
  }
}
</style>
