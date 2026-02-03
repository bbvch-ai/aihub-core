<template>
  <div class="flex flex-col gap-2">
    <SelectButton
      v-if="navItems"
      :model-value="activeNavItem"
      :options="navItems"
      data-key="key"
      option-label="name"
      size="small"
      @update:model-value="toNavItem"
    />
    <div class="flex gap-8">
      <NuxtPage />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { NavItem } from '@core/types/NavItem'

const router = useRouter()
const route = useRoute()
const localePath = useLocalePath()
const { t } = useI18n()

const { agent } = useAgent()

const subPath = (path: string) => {
  return `/service/agents/${route.params.agent_class}-${route.params.agent_id}/${path}`
}

const isActive = (path: string) => {
  return () => {
    const localizedPath = localePath(subPath(path))
    return route.path.startsWith(localizedPath)
  }
}

const navItems = computed<NavItem[]>(() => {
  const items: NavItem[] = [
    { name: t('agent.navigation.basic'), key: 'basic', path: subPath('overview'), isActive: isActive('overview') },
    { name: t('agent.navigation.workflow'), key: 'workflow', path: subPath('workflow'), isActive: isActive('workflow') },
    { name: t('agent.navigation.threads'), key: 'threads', path: subPath('threads'), isActive: isActive('threads') },
    { name: t('agent.navigation.memories'), key: 'memories', path: subPath('memories'), isActive: isActive('memories') },
  ]
  if (agent.value?.is_conversational) {
    items.push({ name: t('agent.navigation.chat'), key: 'chat', path: subPath('chat'), isActive: isActive('chat') },
    )
  }
  return items
})

const toNavItem = (navItem: NavItem) => {
  router.push(localePath(navItem.path))
}

const activeNavItem = computed<NavItem | undefined>(() => {
  return navItems.value?.filter(navItem => navItem.isActive())[0]
})
</script>
