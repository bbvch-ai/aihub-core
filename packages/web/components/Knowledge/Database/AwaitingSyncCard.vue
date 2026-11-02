<template>
  <div class="flex w-full items-center gap-3 rounded-xl border-2 border-dashed border-surface-300 p-4 dark:border-surface-600">
    <div class="flex items-center justify-center p-2">
      <i
        class="pi pi-clock text-surface-400"
        style="font-size: 1.5rem"
      />
    </div>
    <div>
      <h3 class="font-medium text-surface-600 dark:text-surface-400">
        {{ t('knowledge.source.awaiting_sync.title') }}
      </h3>
      <p class="text-sm text-surface-500 dark:text-surface-400">
        {{ t('knowledge.source.awaiting_sync.description') }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n()
</script>
