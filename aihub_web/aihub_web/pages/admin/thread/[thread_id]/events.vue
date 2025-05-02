<template>
  <ProgressBar
    v-if="threadIsLoading || threadEventsAreLoading || !thread || !threadEvents"
    mode="indeterminate"
    style="height: 2px"
  />
  <div
    v-else
  >
    <EventList
      :events="threadEvents"
      :thread="thread"
    />
  </div>
</template>

<script setup lang="ts">
const { thread, threadIsLoading } = useThread()
const { threadEvents, threadEventsAreLoading } = useThreadEvents()
</script>

<style scoped>

</style>
