<template>
  <div class="relative flex flex-col gap-2 p-6">
    <p class="text-xl font-bold">
      Workflow
    </p>
    <div class="h-[900px] w-full">
      <WorkflowVisualization
        v-if="agent"
        :graph-data="agent.network_graph"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAgentsStore } from '@core/stores/useAgentsStore'

import type { AgentDto } from '@core/sdk/client'

const route = useRoute()

const agentStore = useAgentsStore()
const { agents } = storeToRefs(agentStore)

const agent = computed<AgentDto | undefined>(() => agents.value?.find(agent => agent.agent_id === route.params.agent_id && agent.agent_class === route.params.agent_class))
</script>

<style scoped>

</style>
