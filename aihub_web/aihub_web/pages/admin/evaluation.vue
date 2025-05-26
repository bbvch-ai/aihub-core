<template>
  <StructuralScreen>
    <template #top>
      <SelectButton
        v-if="navItems"
        :model-value="activeNavItem"
        :options="navItems"
        data-key="key"
        option-label="name"
        size="small"
        @update:model-value="toNavItem"
      />
    </template>
    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import type { NavItem } from '@core/types/NavItem'

import { useLocalePath } from '#i18n'

const router = useRouter()
const route = useRoute()
const localePath = useLocalePath()

const subPath = (path: string) => {
  return `/admin/evaluation/${path}`
}

onMounted(() => {
  if (route.path === localePath('/admin/evaluation')) {
    router.push(localePath(subPath('experiment')))
  }
})

const isActive = (path: string) => {
  return () => {
    const localizedPath = localePath(subPath(path))
    return route.path.startsWith(localizedPath)
  }
}

const navItems = computed<NavItem[]>(() => {
  return [
    { name: 'Dataset', key: 'dataset', path: subPath('dataset'), isActive: isActive('dataset') },
    { name: 'Experiments', key: 'experiment', path: subPath('experiment'), isActive: isActive('experiment') },
  ]
})

const toNavItem = (navItem: NavItem) => {
  router.push(localePath(navItem.path))
}

const activeNavItem = computed<NavItem | undefined>(() => {
  return navItems.value?.filter(navItem => navItem.isActive())[0]
})
</script>
