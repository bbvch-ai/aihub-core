<template>
  <StructuralScreen>
    <StructuralColumn
      title="Test"
      :loading="agentsAreLoading"
      :nav-items="navItems"
    >
      <AgentList
        :agents="agents"
        @selected="toAgent"
      />
    </StructuralColumn>

    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import type { AgentDto } from '@core/sdk/client'
import type { NavItem } from '@core/types/NavItem'

import { useLocalePath } from '#i18n'

const route = useRoute()
const router = useRouter()
const localePath = useLocalePath()

const { agents, agentsAreLoading } = useAgents()

const toAgent = (agent: AgentDto) => {
  router.push(localePath(`/admin/agent/agent-${agent.agent_id}-${agent.agent_class}/overview`))
}

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
