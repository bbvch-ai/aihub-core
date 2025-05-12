<template>
  <StructuralColumn
    title="Events"
    close-route="/admin/thread"
    :loading="threadIsLoading || threadEventsAreLoading"
  >
    <EventList
      :thread="thread"
      :events="threadEvents"
    />
  </StructuralColumn>
</template>

<script setup lang="ts">
const { thread, threadIsLoading } = useThread()
const { threadEvents, threadEventsAreLoading } = useThreadEvents()
</script>

<style scoped>

</style>
