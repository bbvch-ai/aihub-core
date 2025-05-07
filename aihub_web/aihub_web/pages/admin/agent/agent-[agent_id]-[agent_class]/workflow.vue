<template>
  <ProgressBar
    v-if="agentIsLoading || !agent"
    mode="indeterminate"
    style="height: 2px"
  />
  <div
    v-else
    class="relative flex flex-col gap-2"
  >
    <div class="h-[900px] w-full">
      <WorkflowVisualization
        v-if="agent"
        :graph-data="agent.network_graph"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
const { agent, agentIsLoading } = useAgent()
</script>

<style scoped>

</style>
