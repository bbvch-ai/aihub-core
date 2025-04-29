<template>
  <div class="flex flex-col gap-8">
    <div>
      <p class="text-xl font-bold">
        {{ agent?.agent_config.name }}
      </p>
      <p class="text-sm">
        {{ agent?.agent_config.description }}
      </p>
    </div>
    <div class="flex flex-col gap-2">
      <p class="text-lg font-bold">
        Start Events
      </p>
      <Panel
        v-for="event in agent?.start_events"
        :key="event.event_name"
        :header="event.event_name"
        toggleable
        collapsed
      >
        <div class="text-sm text-surface-700 dark:text-surface-200">
          {{ event.event_schema.description }}
        </div>
      </Panel>
    </div>
    <div class="flex flex-col gap-2">
      <p class="text-lg font-bold">
        Stop Events
      </p>
      <Panel
        v-for="event in agent?.stop_events"
        :key="event.event_name"
        :header="event.event_name"
        toggleable
        collapsed
      >
        <div class="text-sm text-surface-700 dark:text-surface-200">
          {{ event.event_schema.description }}
        </div>
      </Panel>
    </div>
    <div>
      <p class="text-xl font-bold">
        Config
      </p>
      <p class="rounded-lg border border-gray-300 p-3 dark:border-gray-700">
        <pre class="text-sm">{{ agent.agent_config }}</pre>
      </p>
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
