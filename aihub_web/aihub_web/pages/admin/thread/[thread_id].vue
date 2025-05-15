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

import { useLocalePath } from '#i18n'

const router = useRouter()
const route = useRoute()
const localePath = useLocalePath()

const subPath = (path: string) => {
  return `/admin/thread/${route.params.thread_id}/${path}`
}

const isActive = (path: string) => {
  return () => {
    const localizedPath = localePath(subPath(path))
    return route.path.startsWith(localizedPath)
  }
}

const navItems = computed<NavItem[]>(() => {
  return [
    { name: 'Basic', key: 'basic', path: subPath('overview'), isActive: isActive('overview') },
    { name: 'Hierarchy', key: 'hierarchy', path: subPath('hierarchy'), isActive: isActive('hierarchy') },
    { name: 'Chat', key: 'chat', path: subPath('chat'), isActive: isActive('chat') },
    { name: 'Displays', key: 'display', path: subPath('display'), isActive: isActive('display') },
  ]
})

const toNavItem = (navItem: NavItem) => {
  router.push(localePath(navItem.path))
}

const activeNavItem = computed<NavItem | undefined>(() => {
  return navItems.value?.filter(navItem => navItem.isActive())[0]
})
</script>
