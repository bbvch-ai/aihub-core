<template>
  <div>
    <p>Threads</p>
    <div
      v-for="thread in (threads ?? [])"
      :key="thread.id"
    >
      {{ thread.name }}
    </div>
  </div>
</template>

<script setup lang="ts">
import useAgentThreads from '@core/composables/useAgentThreads'

const { data: threads } = useAgentThreads()
</script>

<style scoped>

</style>
