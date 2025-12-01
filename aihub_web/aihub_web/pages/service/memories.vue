<script setup lang="ts">
import { useToast } from 'primevue/usetoast'
import { useI18n } from 'vue-i18n'

import type { NavItem } from '@core/types/NavItem'

import { useLocalePath } from '#i18n'

const router = useRouter()
const route = useRoute()
const localePath = useLocalePath()
const { t } = useI18n()
const toast = useToast()

// Mutations (passed to child pages via NuxtPage)
const { updateMemory } = useUpdateMemory()
const { deleteMemory } = useDeleteMemory()

const subPath = (path: string) => {
  return `/service/memories/${path}`
}

onMounted(() => {
  // Redirect to graph view by default
  if (route.path === localePath('/service/memories')) {
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
  return navItems.value?.filter(navItem => navItem.isActive())[0]
})

const handleCloseDetail = () => {
  // Determine which tab is active and navigate to it
  const activeTab = activeNavItem.value?.key || 'graph'
  router.push({
    path: localePath(`/service/memories/${activeTab}`),
    query: route.query,
  })
}

const handleUpdateMemory = async (memoryId: string, data: string) => {
  try {
    await updateMemory({ memoryId, data })
    toast.add({
      severity: 'success',
      summary: t('memory.update.success.title'),
      detail: t('memory.update.success.message'),
      life: 3000,
    })
  }
  catch (error) {
    console.error('Failed to update memory:', error)
    toast.add({
      severity: 'error',
      summary: t('memory.update.error.title'),
      detail: t('memory.update.error.message'),
      life: 5000,
    })
  }
}

const handleDeleteMemory = async (memoryId: string) => {
  try {
    await deleteMemory({ memoryId })
    toast.add({
      severity: 'success',
      summary: t('memory.delete.success.title'),
      detail: t('memory.delete.success.message'),
      life: 3000,
    })
    handleCloseDetail()
  }
  catch (error) {
    console.error('Failed to delete memory:', error)
    toast.add({
      severity: 'error',
      summary: t('memory.delete.error.title'),
      detail: t('memory.delete.error.message'),
      life: 5000,
    })
  }
}
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
    <NuxtPage
      @close="handleCloseDetail"
      @update="handleUpdateMemory"
      @delete="handleDeleteMemory"
    />
  </StructuralScreen>
</template>
