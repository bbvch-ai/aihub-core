<template>
  <div class="w-full overflow-x-hidden">
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

const subPath = (path: string) => {
  return `/admin/thread/${route.params.thread_id}/${path}`
}

const isActive = (path: string) => {
  return () => {
    const localizedPath = localePath(subPath(path))
    return route.path === localizedPath
  }
}

const navItems = computed<NavItem[]>(() => {
  return [
    { name: 'Basic', key: 'basic', path: subPath('overview'), isActive: isActive('overview') },
    { name: 'Hierarchy', key: 'hierarchy', path: subPath('hierarchy'), isActive: isActive('hierarchy') },
    { name: 'Chat', key: 'chat', path: subPath('chat'), isActive: isActive('chat') },
    { name: 'Events', key: 'events', path: subPath('events'), isActive: isActive('events') },
  ]
})
</script>

<style scoped>

</style>
