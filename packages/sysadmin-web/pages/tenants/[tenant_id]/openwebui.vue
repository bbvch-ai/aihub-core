<template>
  <StructuralColumn :title="tenant?.name ?? t('openwebui_mods.title')" close-route="/tenants" :loading="tenantsAreLoading" size="normal">
    <OpenwebuiModsCatalog :key="tenantId" :tenant-id="tenantId" />
  </StructuralColumn>
</template>

<script setup lang="ts">
import type { TenantResponse } from '~/sdk/client'

definePageMeta({ layout: 'sysadmin' })
const { t } = useI18n()
const route = useRoute()
const localePath = useLocalePath()
const { tenants, tenantsAreLoading } = useTenantAdminList()
const tenantId = computed(() => route.params.tenant_id as string)
const tenant = computed(() => tenants.value?.find((item: TenantResponse) => item.id === tenantId.value))
watch([tenant, tenantsAreLoading], ([value, pending]) => {
  if (!pending && (!value || value.state === 'orphaned')) navigateTo(localePath('/tenants'))
}, { immediate: true })
</script>
