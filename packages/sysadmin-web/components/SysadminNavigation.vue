<template>
  <SelectButton
    :model-value="activeSection"
    :options="sections"
    option-label="label"
    option-value="path"
    :allow-empty="false"
    :aria-label="t('tenant_admin.title')"
    size="small"
    @update:model-value="navigateTo(localePath($event))"
  />
</template>

<script setup lang="ts">
const { t } = useI18n()
const localePath = useLocalePath()
const route = useRoute()

const sections = computed(() => [
  { label: t('tenant_admin.tenants_title'), path: '/tenants' },
  { label: t('openwebui_mods.global.navigation'), path: '/openwebui' },
])
const activeSection = computed(() => route.path.startsWith(localePath('/openwebui')) ? '/openwebui' : '/tenants')
</script>
