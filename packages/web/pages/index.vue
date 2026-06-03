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
// Shown only when the user has no tenants; home-redirect middleware redirects otherwise.
definePageMeta({ middleware: 'home-redirect' })

const { t } = useI18n()
</script>
