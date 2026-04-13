<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('tenant_admin.tenants_title')"
      :loading="tenantsAreLoading"
    >
      <div class="grid grid-cols-2 gap-4 2xl:grid-cols-2">
        <TenantAdminCard
          v-for="tenant in tenants"
          :key="tenant.id"
          :tenant="tenant"
          @click="() => toTenant(tenant)"
        />
        <div
          class="flex min-h-full cursor-pointer flex-col justify-center gap-3 rounded-xl border-2 border-dashed border-surface-300 p-4 hover:border-primary-500 hover:bg-surface-50 dark:border-surface-600 dark:hover:bg-surface-800"
          @click="createModalOpen = true"
        >
          <div class="flex items-center justify-center">
            <div class="flex items-center justify-center p-3">
              <i
                class="pi pi-plus text-surface-400"
                style="font-size: 1.5rem"
              />
            </div>
          </div>
          <div class="text-center">
            <h3 class="font-medium text-surface-600 dark:text-surface-400">
              {{ t('tenant_admin.create_new') }}
            </h3>
          </div>
        </div>
        <Dialog
          v-model:visible="createModalOpen"
          modal
          :header="t('tenant_admin.create_new')"
        >
          <TenantAdminCreate
            @close="createModalOpen = false"
          />
        </Dialog>
      </div>
    </StructuralColumn>
    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import type { TenantResponse } from '@core/sdk/client'

definePageMeta({ layout: 'sysadmin' })

const { t } = useI18n()
const router = useRouter()
const localePath = useLocalePath()

const { tenants, tenantsAreLoading } = useTenantAdminList()

const createModalOpen = ref(false)

const toTenant = (tenant: TenantResponse) => {
  router.push(localePath(`/sysadmin/tenants/${tenant.id}`))
}
</script>
