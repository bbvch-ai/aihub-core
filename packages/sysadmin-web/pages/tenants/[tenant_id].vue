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
    <Message
      v-if="isNotMember"
      severity="warn"
      :closable="false"
    >
      {{ t('tenant_admin.state.not_member_message', { tenantId }) }}
    </Message>
    <div class="flex gap-8">
      <NuxtPage v-if="isOverview || !isNotMember" />
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
const { tenants: memberTenants } = useTenantMemberships()

const tenantId = computed(() => route.params.tenant_id as string)

// The sysadmin role grants admin rights inside a tenant, not membership of it: the tenant-scoped
// roles and users endpoints reject a sysadmin outside the tenant's Keycloak group. Overview only
// reads sysadmin endpoints, so it stays usable either way.
const isNotMember = computed(() =>
  memberTenants.value !== undefined && !memberTenants.value.some(tenant => tenant.id === tenantId.value),
)

const subPath = (path: string) => `/tenants/${route.params.tenant_id}/${path}`

const isActive = (path: string) => () => route.path.startsWith(localePath(subPath(path)))

const navItems = computed<NavItem[]>(() => [
  { name: t('tenant_admin.navigation.overview'), key: 'overview', path: subPath('overview'), isActive: isActive('overview') },
  { name: t('tenant_admin.navigation.roles'), key: 'roles', path: subPath('roles'), isActive: isActive('roles') },
  { name: t('tenant_admin.navigation.users'), key: 'users', path: subPath('users'), isActive: isActive('users') },
])

const isOverview = computed(() => isActive('overview')())

const toNavItem = (navItem: NavItem | null) => {
  if (navItem) router.push(localePath(navItem.path))
}

const activeNavItem = computed<NavItem | undefined>(
  () => navItems.value.find(item => item.isActive()),
)
</script>
