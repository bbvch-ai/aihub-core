<template>
  <div
    class="flex h-full flex-row"
  >
    <NavigationLeft
      :title="$t('agent.availableAgents')"
      :nav-items-map="navItems"
      :loading="agentsAreLoading"
    />
    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
import type { AgentDto } from '@core/sdk/client'
import type { NavItem } from '@core/types/NavItem'

const route = useRoute()
const { agents, agentsAreLoading } = useAgents()

const navItems = computed<Record<string, NavItem[]>>(() => {
  if (agentsAreLoading.value) {
    return {}
  }
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
