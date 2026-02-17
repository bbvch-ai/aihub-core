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
import { useI18n } from 'vue-i18n'

import type { NavItem } from '@core/types/NavItem'

import { useLocalePath } from '#i18n'

const router = useRouter()
const route = useRoute()
const localePath = useLocalePath()
const { t } = useI18n()

const subPath = (path: string) => {
  return `/service/evaluations/${path}`
}

onMounted(() => {
  if (route.path === localePath('service/evaluations')) {
    router.push(localePath(subPath('experiments')))
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
    { name: t('evaluation.dataset.title'), key: 'datasets', path: subPath('datasets'), isActive: isActive('datasets') },
    { name: t('evaluation.experiment.title'), key: 'experiments', path: subPath('experiments'), isActive: isActive('experiments') },
  ]
})

const toNavItem = (navItem: NavItem) => {
  router.push(localePath(navItem.path))
}

const activeNavItem = computed<NavItem | undefined>(() => {
  return navItems.value?.filter(navItem => navItem.isActive())[0]
})
</script>
