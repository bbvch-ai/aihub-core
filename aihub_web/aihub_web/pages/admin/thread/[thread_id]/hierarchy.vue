<template>
  <StructuralColumn
    :title="t('thread.hierarchy.title')"
    close-route="/admin/thread"
    :loading="threadIsLoading"
  >
    <ThreadHierarchy :thread="thread" />
  </StructuralColumn>
</template>

<script setup lang="ts">
const { thread, threadIsLoading } = useThread()
const { t } = useI18n()
</script>
