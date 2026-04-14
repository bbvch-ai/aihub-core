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

definePageMeta({ layout: 'sysadmin' })

const router = useRouter()
const route = useRoute()
const localePath = useLocalePath()
const { t } = useI18n()

const subPath = (path: string) => `/sysadmin/tenants/${route.params.tenant_id}/${path}`

const isActive = (path: string) => () => route.path.startsWith(localePath(subPath(path)))

const navItems = computed<NavItem[]>(() => [
  { name: t('tenant_admin.navigation.overview'), key: 'overview', path: subPath('overview'), isActive: isActive('overview') },
  { name: t('tenant_admin.navigation.roles'), key: 'roles', path: subPath('roles'), isActive: isActive('roles') },
  { name: t('tenant_admin.navigation.users'), key: 'users', path: subPath('users'), isActive: isActive('users') },
])

const toNavItem = (navItem: NavItem | null) => {
  if (navItem) router.push(localePath(navItem.path))
}

const activeNavItem = computed<NavItem | undefined>(
  () => navItems.value.filter(item => item.isActive())[0],
)
</script>
