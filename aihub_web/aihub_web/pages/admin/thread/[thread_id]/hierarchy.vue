<template>
  <ProgressBar
    v-if="threadIsLoading || !thread"
    mode="indeterminate"
    style="height: 2px"
  />
  <div
    v-else
    class="flex flex-col gap-12 p-3"
  >
    <ThreadHierarchy :thread="thread" />
  </div>
</template>

<script setup lang="ts">
const { thread, threadIsLoading } = useThread()
</script>

<style scoped>

</style>
