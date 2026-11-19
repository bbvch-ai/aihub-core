<template>
  <div
    v-if="isAvailable"
    class="flex flex-col gap-1"
  >
    <p class="text-xs text-surface-500 dark:text-surface-400">
      {{ t('tenant_admin.llm_usage.title') }}
    </p>
    <div>
      <Button
        :label="t('tenant_admin.llm_usage.open_tenant')"
        icon="pi pi-external-link"
        icon-pos="right"
        severity="secondary"
        size="small"
        as="a"
        :href="usageUrl"
        target="_blank"
        rel="noopener noreferrer"
      />
    </div>
    <p class="text-sm">
      {{ t('tenant_admin.llm_usage.pick_tenant', { name: tenantName }) }}
      <span class="font-mono">{{ tenantId }}</span>
    </p>
    <p class="text-xs text-surface-500 dark:text-surface-400">
      {{ t('tenant_admin.llm_usage.chf_note') }}
    </p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  tenantId: string
  tenantName: string
}>()

const { t } = useI18n()
const { usageUrl, isAvailable } = useLiteLlmUsage()
</script>
