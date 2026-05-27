<!-- SPDX-License-Identifier: LicenseRef-Proprietary -->
<template>
  <div class="flex min-h-screen w-full flex-col bg-white dark:bg-surface-900">
    <div class="fixed z-50 flex h-[50px] w-full items-center justify-between border-b border-surface-200 bg-surface-50 px-4 dark:border-surface-700 dark:bg-surface-950">
      <div class="flex items-center gap-3">
        <i class="pi pi-building text-lg text-primary" />
        <h1 class="text-sm font-semibold text-surface-900 dark:text-surface-50">
          {{ t('tenant_admin.title') }}
        </h1>
      </div>
      <div class="flex items-center gap-2">
        <Button
          v-tooltip.bottom="{ value: t('bar.toggle_dark_mode'), showDelay: 0 }"
          :icon="isDark ? 'pi pi-sun' : 'pi pi-moon'"
          severity="secondary"
          variant="text"
          rounded
          :aria-label="t('bar.toggle_dark_mode')"
          @click="toggleDarkMode"
        />
        <Button
          :label="t('tenant_admin.exit')"
          icon="pi pi-sign-out"
          severity="secondary"
          size="small"
          @click="exitSysAdmin"
        />
      </div>
    </div>
    <div class="mt-[50px] w-full">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n()
const { exitToMainApp } = useMainAppNavigation()

const isDark = useDarkMode()

function toggleDarkMode() {
  isDark.value = !isDark.value
}

// "Exit" leaves the sysadmin plane entirely — cross-origin back to the main
// app's tenant selector. A local navigateTo() would be bounced back here by
// the confinement middleware (sysadmin-web has no /select-tenant of its own
// that the middleware permits).
function exitSysAdmin() {
  exitToMainApp()
}
</script>
