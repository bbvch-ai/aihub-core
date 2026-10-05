<template>
  <StructuralScreen>
    <template #top>
      <div class="flex flex-col gap-1">
        <h1 class="text-2xl font-semibold">
          {{ t('userFiles.title') }}
        </h1>
        <p class="text-sm text-surface-500">
          {{ t('userFiles.description') }}
        </p>
      </div>
    </template>
    <UserFilesBrowser />
  </StructuralScreen>
</template>

<script setup lang="ts">
const { t } = useI18n()
</script>
