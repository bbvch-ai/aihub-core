<template>
  <StructuralColumn
    :title="t('agent.workflow.title')"
    close-route="/service/agents"
    :loading="agentInstanceIsLoading"
  >
    <div class="h-[900px] w-full">
      <WorkflowVisualization
        v-if="agentInstance && agentInstance.network_graph"
        :graph-data="agentInstance.network_graph"
      />
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
const { agentInstance, agentInstanceIsLoading } = useAgentInstance()
const { t } = useI18n()
</script>
