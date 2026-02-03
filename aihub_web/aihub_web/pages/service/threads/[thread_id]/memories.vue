<template>
  <MemoryManagementPage
    translation-prefix="thread"
    :context-name="thread?.name ?? ''"
    :context-loading="threadIsLoading"
    :memory-context="{
      type: 'user',
      thread_id: route.params.thread_id as string,
    }"
    :base-path="`/service/threads/${route.params.thread_id}/memories`"
  />
</template>

<script setup lang="ts">
const route = useRoute()

// Get thread info
const { thread, threadIsLoading } = useThread()
</script>
