<template>
  <StructuralColumn
    title="Hierarchy"
    close-route="/admin/thread"
    :loading="threadIsLoading"
  >
    <ThreadHierarchy :thread="thread" />
  </StructuralColumn>
</template>

<script setup lang="ts">
const { thread, threadIsLoading } = useThread()
</script>
