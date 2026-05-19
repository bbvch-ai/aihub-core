<template>
  <div class="flex items-center gap-2">
    <button
      v-tooltip.bottom="{ value: t('tenant.switcher_label') }"
      class="flex max-w-48 items-center gap-1.5 rounded px-2 py-1 text-sm text-surface-600 transition-colors dark:text-surface-300"
      :class="hasMultipleTenants || isSysAdmin ? 'cursor-pointer hover:bg-surface-100 dark:hover:bg-surface-800' : 'cursor-default'"
      :disabled="!hasMultipleTenants && !isSysAdmin"
      :aria-label="t('tenant.switcher_label')"
      @click="toggle"
    >
      <i class="pi pi-building shrink-0 text-xs" />
      <span class="truncate">{{ currentTenantDisplayName }}</span>
      <i
        v-if="hasMultipleTenants || isSysAdmin"
        class="pi pi-chevron-down shrink-0 text-xs opacity-60"
      />
    </button>

    <Popover ref="popoverRef">
      <div class="flex w-64 flex-col gap-2 p-2">
        <p class="text-sm font-bold text-muted-color">
          {{ t('tenant.switcher_label') }}
        </p>
        <div
          v-for="tenant in tenants"
          :key="tenant.id"
          class="cursor-pointer rounded-md px-3 py-2 transition-colors hover:bg-surface-100 dark:hover:bg-surface-700"
          :class="{ 'bg-primary/10 font-semibold': tenant.id === tenantId }"
          @click="onSelect(tenant)"
        >
          <p class="text-sm">
            {{ tenant.name }}
          </p>
          <p
            v-if="tenant.description"
            class="text-xs text-muted-color"
          >
            {{ tenant.description }}
          </p>
        </div>

        <div
          v-if="isSysAdmin"
          class="border-t border-surface-200 pt-2 dark:border-surface-700"
        >
          <div
            class="flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 transition-colors hover:bg-surface-100 dark:hover:bg-surface-700"
            @click="enterSysAdmin"
          >
            <i class="pi pi-cog text-xs text-primary" />
            <p class="text-sm">
              {{ t('tenant_admin.title') }}
            </p>
          </div>
        </div>

        <p
          v-if="!tenants?.length && !tenantsAreLoading"
          class="text-sm text-muted-color"
        >
          {{ t('tenant.no_tenant_description') }}
        </p>
        <ProgressSpinner
          v-if="tenantsAreLoading"
          style="width: 1.5rem; height: 1.5rem"
        />
      </div>
    </Popover>
  </div>
</template>

<script setup lang="ts">
import Popover from 'primevue/popover'

import type { TenantMembershipDto } from '@core/sdk/client'

const { t } = useI18n()
const localePath = useLocalePath()
const { tenantId, setTenant } = useTenant()
const { tenants, tenantsAreLoading, isSysAdmin } = useTenantMemberships()

const hasMultipleTenants = computed(() => (tenants.value?.length ?? 0) > 1)
const currentTenantDisplayName = computed(() => {
  const current = tenants.value?.find(t => t.id === tenantId.value)
  return current?.name ?? tenantId.value ?? ''
})
const popoverRef = ref<InstanceType<typeof Popover>>()

function toggle(event: Event) {
  popoverRef.value?.toggle(event)
}

async function onSelect(tenant: TenantMembershipDto) {
  popoverRef.value?.hide()
  await setTenant(tenant.id)
}

function enterSysAdmin() {
  popoverRef.value?.hide()
  navigateTo(localePath('/sysadmin/tenants'), { replace: true })
}
</script>
