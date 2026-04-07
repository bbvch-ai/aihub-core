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
    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
import type { NavItem } from '@core/types/NavItem'

const router = useRouter()
const route = useRoute()
const tenantPath = useTenantPath()
const { t } = useI18n()

const subPath = (path: string) => {
  return `/service/knowledge/${route.params.db}/${route.params.namespace}/${route.params.document_id}/${path}`
}

const isActive = (path: string) => {
  return () => {
    const localizedPath = tenantPath(subPath(path))
    return route.path.startsWith(localizedPath)
  }
}

const navItems = computed<NavItem[]>(() => [
  { name: t('knowledge.navigation.document.basic'), key: 'basic', path: subPath('overview'), isActive: isActive('overview') },
  { name: t('knowledge.navigation.document.nodes'), key: 'nodes', path: subPath('nodes'), isActive: isActive('nodes') },
  { name: t('knowledge.navigation.document.summary'), key: 'summary', path: subPath('summary'), isActive: isActive('summary') },
])

const toNavItem = (navItem: NavItem) => {
  router.push(tenantPath(navItem.path))
}

const activeNavItem = computed<NavItem | undefined>(() => {
  return navItems.value?.filter(navItem => navItem.isActive())[0]
})
</script>
