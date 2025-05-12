<template>
  <StructuralColumn
    title="Events"
    close-route="/admin/thread"
    :loading="threadIsLoading || threadEventsAreLoading"
  >
    <EventList
      :events="threadEvents"
      :thread="thread"
    />
  </StructuralColumn>
</template>

<script setup lang="ts">
const { thread, threadIsLoading } = useThread()
const { threadEvents, threadEventsAreLoading } = useThreadEvents()
</script>

<style scoped>

</style>
