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
const { tenantPath } = useTenantPath()
const { t } = useI18n()

const subPath = (path: string) => {
  return `/service/threads/${route.params.thread_id}/${path}`
}

const isActive = (path: string) => {
  return () => {
    const localizedPath = tenantPath(subPath(path))
    return route.path.startsWith(localizedPath)
  }
}

const navItems = computed<NavItem[]>(() => {
  return [
    { name: t('thread.navigation.basic'), key: 'basic', path: subPath('overview'), isActive: isActive('overview') },
    { name: t('thread.navigation.hierarchy'), key: 'hierarchy', path: subPath('hierarchy'), isActive: isActive('hierarchy') },
    { name: t('thread.navigation.chat'), key: 'chat', path: subPath('chat'), isActive: isActive('chat') },
    { name: t('thread.navigation.display'), key: 'display', path: subPath('display'), isActive: isActive('display') },
    { name: t('thread.navigation.memories'), key: 'memories', path: subPath('memories'), isActive: isActive('memories') },
  ]
})

const toNavItem = (navItem: NavItem) => {
  router.push(tenantPath(navItem.path))
}

const activeNavItem = computed<NavItem | undefined>(() => {
  return navItems.value?.filter(navItem => navItem.isActive())[0]
})
</script>
