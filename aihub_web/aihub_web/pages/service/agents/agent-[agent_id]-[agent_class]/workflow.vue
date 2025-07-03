<template>
  <StructuralColumn
    :title="t('agent.workflow.title')"
    close-route="/service/agents"
    :loading="agentIsLoading"
  >
    <div class="h-[900px] w-full">
      <WorkflowVisualization
        v-if="agent && agent.network_graph"
        :graph-data="agent.network_graph"
      />
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
const { agent, agentIsLoading } = useAgent()
const { t } = useI18n()
</script>
