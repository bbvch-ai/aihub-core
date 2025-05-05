<template>
  <div class="w-full">
    <NavigationTop
      :nav-items="navItems"
    />
    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
import type { NavItem } from '@core/types/NavItem'

import { useLocalePath } from '#i18n'

const route = useRoute()
const localePath = useLocalePath()
const { t } = useI18n()

const { agent } = useAgent()

const subPath = (path: string) => {
  return `/admin/agent/agent-${route.params.agent_id}-${route.params.agent_class}/${path}`
}

const isActive = (path: string) => {
  return () => {
    const localizedPath = localePath(subPath(path))
    return route.path === localizedPath
  }
}

const navItems = computed<NavItem[]>(() => {
  const items: NavItem[] = [
    { name: t('agent.navigation.basic'), key: 'basic', path: subPath('overview'), isActive: isActive('overview') },
    { name: t('agent.navigation.workflow'), key: 'workflow', path: subPath('workflow'), isActive: isActive('workflow') },
    { name: t('agent.navigation.threads'), key: 'threads', path: subPath('threads'), isActive: isActive('threads') },
  ]
  if (agent.value?.is_conversational) {
    items.push({ name: t('agent.navigation.chat'), key: 'chat', path: subPath('chat'), isActive: isActive('chat') },
    )
  }
  return items
})
</script>

<style scoped>

</style>
