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
const localePath = useLocalePath()
const { t } = useI18n()

const { processInstance } = useProcessInstance()

const subPath = (path: string) => {
  return `/service/processes/${route.params.process_class}-${route.params.process_id}/${path}`
}

const isActive = (path: string) => {
  return () => {
    const localizedPath = localePath(subPath(path))
    return route.path.startsWith(localizedPath)
  }
}

const hasConfigForm = computed(() => {
  return processInstance.value?.form && processInstance.value.form.length > 0
})

const navItems = computed<NavItem[]>(() => {
  const items: NavItem[] = [
    { name: t('process.navigation.overview'), key: 'overview', path: subPath('overview'), isActive: isActive('overview') },
    { name: t('process.navigation.walkthroughs'), key: 'walkthroughs', path: subPath('walkthroughs'), isActive: isActive('walkthroughs') },
    { name: t('process.navigation.start'), key: 'start', path: subPath('start'), isActive: isActive('start') },
  ]
  if (hasConfigForm.value) {
    items.push({ name: t('process.navigation.configuration'), key: 'configuration', path: subPath('configuration'), isActive: isActive('configuration') })
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
