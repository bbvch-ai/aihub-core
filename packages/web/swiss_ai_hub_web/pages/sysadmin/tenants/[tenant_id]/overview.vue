<template>
  <StructuralColumn
    :title="tenant?.name"
    close-route="/sysadmin/tenants"
    :loading="tenantsAreLoading"
    size="normal"
  >
    <div
      v-if="clonedTenant"
      class="flex flex-col gap-4"
    >
      <div class="flex flex-col gap-1">
        <label class="text-xs text-surface-500 dark:text-surface-400">
          {{ t('tenant_admin.tenant_id') }}
        </label>
        <span class="font-mono text-sm">{{ tenantId }}</span>
      </div>
      <TenantAdminEdit
        v-model="clonedTenant"
      />
      <div class="flex justify-end">
        <Button
          type="button"
          :label="t('tenant_admin.save')"
          icon="pi pi-save"
          :disabled="!clonedTenant.name"
          @click="saveTenant"
        />
      </div>
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
import { cloneDeep } from 'lodash-es'

import type { TenantResponse, UpdateTenantRequest } from '@core/sdk/client'

definePageMeta({ layout: 'sysadmin' })

const route = useRoute()
const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()
const toast = useToast()

const { tenants, tenantsAreLoading } = useTenantAdminList()
const { updateTenant } = useUpdateTenant()

const tenantId = computed(() => route.params.tenant_id as string)

const tenant = computed(() =>
  tenants.value?.find((tn: TenantResponse) => tn.id === tenantId.value),
)

const clonedTenant = ref<UpdateTenantRequest | null>(null)

// Redirect if tenant is missing or orphaned (edit view is not allowed for orphans).
watch([tenant, tenantsAreLoading], ([newTenant, loading]) => {
  if (loading) return
  if (!newTenant || newTenant.state === 'orphaned') {
    router.push(localePath('/sysadmin/tenants'))
    return
  }
  clonedTenant.value = cloneDeep({
    name: newTenant.name,
    description: newTenant.description,
    access_rules: newTenant.access_rules,
  })
}, { immediate: true })

const saveTenant = async () => {
  if (!clonedTenant.value) return
  await updateTenant({ tenantId: tenantId.value, data: clonedTenant.value })
  toast.add({ severity: 'success', summary: t('tenant_admin.tenant_saved.summary'), detail: t('tenant_admin.tenant_saved.detail'), life: 3000 })
}
</script>
