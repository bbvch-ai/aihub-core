<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { NavItem } from '@core/types/NavItem'

import { useLocalePath } from '#i18n'

const router = useRouter()
const route = useRoute()
const localePath = useLocalePath()
const { t } = useI18n()

const subPath = (path: string) => {
  return `/service/organization-memories/${path}`
}

onMounted(() => {
  // Redirect to graph view by default
  if (route.path === localePath('/service/organization-memories')) {
    router.push({
      path: localePath(subPath('graph')),
      query: route.query,
    })
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
    { name: t('memory.graph.title'), key: 'graph', path: subPath('graph'), isActive: isActive('graph') },
    { name: t('memory.list.title'), key: 'list', path: subPath('list'), isActive: isActive('list') },
  ]
})

const toNavItem = (navItem: NavItem) => {
  router.push({
    path: localePath(navItem.path),
    query: route.query,
  })
}

const activeNavItem = computed<NavItem | undefined>(() => {
  return navItems.value?.find(navItem => navItem.isActive())
})
</script>

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
