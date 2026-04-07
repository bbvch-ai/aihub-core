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

const REDIRECT_KEY = 'aihub_redirect_after_login'

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

    // Check if we have a stored redirect URL from before login (e.g. user had a
    // direct link with a tenant already in the path)
    const storedRedirect = sessionStorage.getItem(REDIRECT_KEY)
    sessionStorage.removeItem(REDIRECT_KEY)

    if (storedRedirect && storedRedirect !== '/') {
      // The stored redirect already contains the tenant — go there directly
      await navigateTo(storedRedirect, { replace: true })
      return
    }

    // Single tenant: auto-select and go
    if (tenantsResponse.length === 1) {
      const tenant = tenantsResponse[0]
      await navigateTo(localePath(`/${tenant.id}/service/openai`), { replace: true })
      return
    }

    // Multiple tenants and no stored redirect: show tenant selection
    await navigateTo(localePath('/select-tenant'), { replace: true })
  }
  catch {
    tenantsAreLoading.value = false
  }
})
</script>
