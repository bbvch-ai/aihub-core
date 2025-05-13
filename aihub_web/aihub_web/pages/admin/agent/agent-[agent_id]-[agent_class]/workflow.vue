<template>
  <StructuralColumn
    title="Workflow"
    close-route="/admin/agent"
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
</script>

<style scoped>

</style>
