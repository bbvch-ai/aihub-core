<template>
  <div class="flex items-center gap-2">
    <Button
      v-tooltip.bottom="{ value: t('tenant.switcher_label') }"
      :label="tenantName ?? ''"
      icon="pi pi-building"
      variant="text"
      size="small"
      :aria-label="t('tenant.switcher_label')"
      @click="toggle"
    />

    <Popover ref="popoverRef">
      <div class="flex w-64 flex-col gap-2 p-2">
        <p class="text-sm font-bold text-muted-color">
          {{ t('tenant.switcher_label') }}
        </p>
        <div
          v-for="tenant in tenants"
          :key="tenant.id"
          class="cursor-pointer rounded-md px-3 py-2 transition-colors hover:bg-surface-100 dark:hover:bg-surface-700"
          :class="{ 'bg-primary/10 font-semibold': tenant.name === tenantName }"
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
import type { TenantMembershipDto } from '@core/sdk/client'

const { t } = useI18n()
const { tenantName } = useTenantFromRoute()
const { tenants, tenantsAreLoading } = useTenantMemberships()
const { switchTenant } = useTenantSwitch()

const popoverRef = ref()

function toggle(event: Event) {
  popoverRef.value?.toggle(event)
}

async function onSelect(tenant: TenantMembershipDto) {
  popoverRef.value?.hide()
  if (tenant.name !== tenantName.value) {
    await switchTenant(tenant.id, tenant.name)
  }
}
</script>
