<template>
  <div class="flex h-screen items-center justify-center">
    <div class="w-full max-w-2xl px-4">
      <h1 class="mb-2 text-center text-2xl font-bold">
        {{ t('tenant.select_title') }}
      </h1>
      <p class="mb-8 text-center text-muted-color">
        {{ t('tenant.select_description') }}
      </p>

      <ProgressSpinner v-if="tenantsAreLoading" />

      <div
        v-else
        class="grid grid-cols-1 gap-4 md:grid-cols-2"
      >
        <Card
          v-for="tenant in tenants"
          :key="tenant.id"
          class="cursor-pointer transition-shadow hover:shadow-lg"
          @click="selectTenant(tenant)"
        >
          <template #title>
            {{ tenant.name }}
          </template>
          <template #content>
            <p class="text-sm text-muted-color">
              {{ tenant.description }}
            </p>
          </template>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { setMyActiveTenant } from '@core/sdk/client'

import type { TenantMembershipDto } from '@core/sdk/client'

definePageMeta({ layout: 'anonymous' })

const { t } = useI18n()
const localePath = useLocalePath()
const { tenants, tenantsAreLoading } = useTenantMemberships()

async function selectTenant(tenant: TenantMembershipDto) {
  await setMyActiveTenant({ composable: '$fetch', body: { tenant_id: tenant.id } })
  await navigateTo(localePath(`/${tenant.name}/service/openai`), { replace: true })
}
</script>
