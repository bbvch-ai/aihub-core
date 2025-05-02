<template>
  <div
    class="overflow-auto rounded-lg border border-surface-200 dark:border-surface-700"
  >
    <div class="">
      <div class="flex flex-col gap-6 p-6">
        <div>
          <p class="text-2xl font-bold">
            {{ agent?.agent_config.name }}
          </p>
          <p class="text-sm">
            {{ agent?.agent_config.description }}
          </p>
        </div>
        <div>
          <p class="text-xl font-bold">
            Events
          </p>
          <div
            v-for="startEvent in startEvents"
            :key="startEvent.event_name"
          >
            <component
              :is="startEventComponents[startEvent.event_name]"
              v-if="startEvent.event_name in startEventComponents"
            />
          </div>
        </div>
        <div>
          <p class="text-xl font-bold">
            Workflow
            <Button
              rounded
              variant="text"
              icon="pi pi-window-maximize"
              @click="workflowFullscreen = true"
            />
          </p>
        </div>
        <Drawer
          v-model:visible="workflowFullscreen"
          header="Workflow"
          position="full"
        >
          <WorkflowVisualization
            v-if="agent"
            :graph-data="agent.network_graph"
          />
        </Drawer>
        <div class="h-[400px] w-full">
          <WorkflowVisualization
            v-if="agent"
            :graph-data="agent.network_graph"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import UserMessageEvent from '@core/components/Event/Form/UserMessageEvent.vue'
import { useAgentsStore } from '@core/stores/useAgentsStore'

import type { AgentDto, EventSpecs } from '@core/sdk/client'

const route = useRoute()

const agentStore = useAgentsStore()
const { agents } = storeToRefs(agentStore)

const agent = computed<AgentDto | undefined>(() => agents.value?.find(agent => agent.agent_id === route.params.agent_id && agent.agent_class === route.params.agent_class))

const startEvents = computed<EventSpecs[]>(() => {
  return agent.value?.start_events ?? []
})

const startEventComponents = { UserMessageEvent }

const workflowFullscreen = ref(false)
</script>

<style scoped>

</style>
