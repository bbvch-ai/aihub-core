<template>
  <div
    class="border-gray-200 dark:border-gray-700 border rounded-lg overflow-auto"
  >
    <div class="bg-white dark:bg-black">
      <div class="flex flex-col gap-2 p-6">
        <p class="text-3xl font-bold">
          {{ agent?.agent_config.name }}
        </p>
        <p class="text-sm">
          {{ agent?.agent_config.description }}
        </p>
      </div>
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
