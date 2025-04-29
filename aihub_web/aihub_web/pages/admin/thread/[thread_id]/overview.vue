<template>
  <div v-if="thread">
    <ThreadInfo
      :thread="thread"
    />
    <div class="max-w-16">
      <pre>{{ thread }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import useThread from '@core/composables/useThread'

const { data: thread } = useThread()
</script>

<style scoped>

</style>
