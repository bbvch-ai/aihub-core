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
import { getMyTenants } from '@core/sdk/client'

const REDIRECT_KEY = 'aihub_redirect_after_login'

const { t } = useI18n()
const localePath = useLocalePath()

const tenantsAreLoading = ref(true)
const tenants = ref<{ id: string }[] | null>(null)

onMounted(async () => {
  try {
    const response = await getMyTenants({ composable: '$fetch' })
    tenants.value = response.tenants

    if (!response.tenants?.length) {
      tenantsAreLoading.value = false
      return
    }

    const storedRedirect = sessionStorage.getItem(REDIRECT_KEY)
    sessionStorage.removeItem(REDIRECT_KEY)

    if (storedRedirect && storedRedirect !== '/') {
      await navigateTo(storedRedirect, { replace: true })
      return
    }

    if (response.tenants.length === 1) {
      const tenant = response.tenants[0]
      await navigateTo(localePath(`/${tenant.id}/service/openai`), { replace: true })
      return
    }

    await navigateTo(localePath('/select-tenant'), { replace: true })
  }
  catch {
    tenantsAreLoading.value = false
  }
})
</script>
