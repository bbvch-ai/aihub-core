<template>
  <div class="w-full">
    <NavigationTop
      :nav-items="navItems"
    />
    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
import { useAgentsStore } from '@core/stores/useAgentsStore'

import type { AgentDto } from '@core/sdk/client'
import type { NavItem } from '@core/types/NavItem'

import { useLocalePath } from '#i18n'

const route = useRoute()
const localePath = useLocalePath()

const agentStore = useAgentsStore()
const { agents } = storeToRefs(agentStore)

const agent = computed<AgentDto | undefined>(() => agents.value?.find(agent => agent.agent_id === route.params.agent_id && agent.agent_class === route.params.agent_class))

const subPath = (path: string) => {
  return `/admin/agent/agent-${agent.value?.agent_id}-${agent.value?.agent_class}/${path}`
}

const isActive = (path: string) => {
  return () => {
    const localizedPath = localePath(subPath(path))
    console.log(localizedPath)
    return route.path === localizedPath
  }
}

const navItems = computed<NavItem[]>(() => {
  const items: NavItem[] = [
    { name: 'Basic', key: 'basic', path: subPath('overview'), isActive: isActive('overview') },
    { name: 'Workflow', key: 'workflow', path: subPath('workflow'), isActive: isActive('workflow') },
  ]
  if (agent.value?.is_conversational) {
    items.push({ name: 'Chat', key: 'chat', path: subPath('chat'), isActive: isActive('chat') },
    )
  }
  return items
})
</script>

<style scoped>

</style>
