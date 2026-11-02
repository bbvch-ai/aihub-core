<template>
  <StructuralColumn
    :title="tenant?.name"
    close-route="/tenants"
    :loading="tenantsAreLoading"
    size="normal"
  >
    <div
      v-if="clonedTenant"
      class="flex flex-col gap-4"
    >
      <div class="flex flex-col gap-1">
        <p class="text-xs text-surface-500 dark:text-surface-400">
          {{ t('tenant_admin.tenant_id') }}
        </p>
        <span class="font-mono text-sm">{{ tenantId }}</span>
      </div>
      <FormKit
        :key="tenantId"
        type="form"
        :actions="false"
        @submit="saveTenant"
      >
        <TenantAdminEdit v-model="clonedTenant" />
        <Message
          v-if="saveFailed"
          severity="error"
          :closable="false"
          class="mt-4"
        >
          {{ t('tenant_admin.save_error') }}
        </Message>
        <div class="mt-4 flex justify-end">
          <Button
            type="submit"
            :label="t('tenant_admin.save')"
            icon="pi pi-save"
            :loading="isSaving"
            :disabled="!clonedTenant.name || isSaving"
          />
        </div>
      </FormKit>
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
import { cloneDeep } from 'lodash-es'

import type { TenantResponse, UpdateTenantMetadataRequest } from '~/sdk/client'

definePageMeta({ layout: 'sysadmin' })

const route = useRoute()
const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()
const toast = useToast()

const { tenants, tenantsAreLoading } = useTenantAdminList()
const { updateTenantMetadata, isSaving } = useUpdateTenantMetadata()

const tenantId = computed(() => route.params.tenant_id as string)

const tenant = computed(() =>
  tenants.value?.find((tn: TenantResponse) => tn.id === tenantId.value),
)

const clonedTenant = ref<UpdateTenantMetadataRequest | null>(null)
const saveFailed = ref(false)

// Redirect if tenant is missing or orphaned (edit view is not allowed for orphans).
watch([tenant, tenantsAreLoading], ([newTenant, loading]) => {
  if (loading) return
  if (!newTenant || newTenant.state === 'orphaned') {
    router.push(localePath('/tenants'))
    return
  }
  clonedTenant.value = cloneDeep({
    name: newTenant.name,
    description: newTenant.description,
    access_rules: newTenant.access_rules,
    chat_disclaimer: newTenant.chat_disclaimer,
  })
  saveFailed.value = false
}, { immediate: true })

const saveTenant = async () => {
  if (!clonedTenant.value || isSaving.value) return
  saveFailed.value = false
  try {
    await updateTenantMetadata({ tenantId: tenantId.value, data: clonedTenant.value })
    toast.add({ severity: 'success', summary: t('tenant_admin.tenant_saved.summary'), detail: t('tenant_admin.tenant_saved.detail'), life: 3000 })
  }
  catch {
    saveFailed.value = true
  }
}
</script>
