<template>
  <div class="flex h-screen items-center justify-center">
    <ProgressSpinner v-if="tenantsAreLoading" />
    <div
      v-else-if="!tenants?.length"
      class="text-center"
    >
      <h1 class="mb-4 text-2xl font-bold">
        {{ t('tenant.no_tenant_title') }}
      </h1>
      <p class="text-muted-color">
        {{ t('tenant.no_tenant_description') }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { getMyActiveTenant, getMyTenants } from '@core/sdk/client'

const { t } = useI18n()
const localePath = useLocalePath()

const tenantsAreLoading = ref(true)
const tenants = ref<Awaited<ReturnType<typeof getMyTenants>>['data']>(null)

onMounted(async () => {
  try {
    const tenantsResponse = await getMyTenants({ composable: '$fetch' })
    tenants.value = tenantsResponse

    if (!tenantsResponse?.length) {
      tenantsAreLoading.value = false
      return
    }

    if (tenantsResponse.length === 1) {
      const tenant = tenantsResponse[0]
      await navigateTo(localePath(`/${tenant.name}/service/openai`), { replace: true })
      return
    }

    // Multiple tenants: try to use active tenant
    try {
      const activeTenant = await getMyActiveTenant({ composable: '$fetch' })
      if (activeTenant) {
        await navigateTo(localePath(`/${activeTenant.name}/service/openai`), { replace: true })
        return
      }
    }
    catch {
      // No active tenant set — show selection
    }

    await navigateTo(localePath('/select-tenant'), { replace: true })
  }
  catch {
    tenantsAreLoading.value = false
  }
})
</script>
