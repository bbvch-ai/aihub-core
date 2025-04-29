<template>
  <div
    class="flex h-full flex-row"
  >
    <NavigationLeft
      title="Available Agents"
      :nav-items-map="navItems"
    />
    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
import { useAgentsStore } from '@core/stores/useAgentsStore'

import type { AgentDto } from '@core/sdk/client'
import type { NavItem } from '@core/types/NavItem'

const route = useRoute()
const agentStore = useAgentsStore()
const { agents } = storeToRefs(agentStore)

const navItems = computed<Record<string, NavItem[]>>(() => {
  const typeMap: Record<string, NavItem[]> = {}
  agents.value?.forEach((agent: AgentDto) => {
    if (!(agent.agent_class in typeMap)) {
      typeMap[agent.agent_class] = []
    }
    typeMap[agent.agent_class].push({
      name: agent.agent_config.name,
      key: `${agent.agent_class}${agent.agent_id}`,
      path: `/admin/agent/agent-${agent.agent_id}-${agent.agent_class}/overview`,
      isActive: () => route.params.agent_id === agent.agent_id && route.params.agent_class === agent.agent_class,
    })
  })
  return typeMap
})
</script>

<style scoped>

</style>
