<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('tenant_admin.tenants_title')"
      :loading="tenantsAreLoading"
    >
      <Message
        v-if="isKeycloakUnreachable"
        severity="error"
        :closable="false"
        class="mb-4"
      >
        {{ t('tenant_admin.keycloak_unreachable') }}
      </Message>

      <div class="grid grid-cols-2 gap-4 2xl:grid-cols-2">
        <TenantAdminCard
          v-for="tenant in tenants"
          :key="tenant.id"
          :tenant="tenant"
          :can-delete="(tenants?.length ?? 0) > 1"
          @click="() => toTenant(tenant)"
        />

        <div
          v-tooltip.top="canConfigure ? undefined : { value: t('tenant_admin.configure.empty_unconfigured') }"
          class="flex min-h-full flex-col justify-center gap-3 rounded-xl border-2 border-dashed p-4"
          :class="canConfigure
            ? 'cursor-pointer border-surface-300 hover:border-primary-500 hover:bg-surface-50 dark:border-surface-600 dark:hover:bg-surface-800'
            : 'cursor-not-allowed border-surface-200 opacity-50 dark:border-surface-700'"
          @click="openConfigureModal"
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
          v-model:visible="configureModalOpen"
          modal
          :header="t('tenant_admin.configure.title')"
          class="w-full max-w-xl"
        >
          <TenantAdminConfigure
            @close="configureModalOpen = false"
          />
        </Dialog>
      </div>
    </StructuralColumn>
    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import type { TenantResponse } from '@core/sdk/client'

definePageMeta({ layout: 'sysadmin', middleware: 'sysadmin' })

const { t } = useI18n()
const router = useRouter()
const localePath = useLocalePath()

const { tenants, tenantsAreLoading, error } = useTenantAdminList()
const { unconfiguredTenantIds } = useUnconfiguredTenantIds()

const configureModalOpen = ref(false)

const isKeycloakUnreachable = computed(() => {
  const err = error.value as { statusCode?: number, status?: number } | null | undefined
  const statusCode = err?.statusCode ?? err?.status
  return statusCode === 503
})

const canConfigure = computed(() => (unconfiguredTenantIds.value?.length ?? 0) > 0)

const openConfigureModal = () => {
  if (canConfigure.value) {
    configureModalOpen.value = true
  }
}

const toTenant = (tenant: TenantResponse) => {
  if (tenant.state === 'orphaned') return
  router.push(localePath(`/sysadmin/tenants/${tenant.id}/overview`))
}
</script>
