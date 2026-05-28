<!-- SPDX-License-Identifier: LicenseRef-Proprietary -->
<template>
  <div class="flex h-screen flex-col items-center justify-center gap-6 bg-zinc-900 px-6 text-center text-white">
    <div class="flex h-16 w-16 items-center justify-center rounded-full bg-red-900/40 text-red-300">
      <i class="pi pi-lock text-3xl" />
    </div>
    <div class="max-w-lg space-y-3">
      <h1 class="text-2xl font-semibold">
        {{ t('sysadmin_required.title') }}
      </h1>
      <p class="text-surface-300">
        {{ t('sysadmin_required.description') }}
      </p>
    </div>
    <div class="flex gap-3">
      <Button
        :label="t('sysadmin_required.exit')"
        icon="pi pi-arrow-left"
        @click="exitToMainApp"
      />
      <Button
        :label="t('sysadmin_required.logout')"
        icon="pi pi-sign-out"
        severity="secondary"
        outlined
        @click="logout"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'anonymous',
})

const { t } = useI18n()
const { exitToMainApp } = useMainAppNavigation()
const { logout } = useAuth()
</script>
