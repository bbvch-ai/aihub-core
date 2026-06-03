<template>
  <div class="flex h-screen items-center justify-center">
    <div class="text-center">
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
// Tenant resolution + redirect happens in the `home-redirect` route middleware
// (see middleware/home-redirect.ts). This page only renders when the user has
// no tenants — otherwise the middleware redirects before it mounts.
definePageMeta({ middleware: 'home-redirect' })

const { t } = useI18n()
</script>
