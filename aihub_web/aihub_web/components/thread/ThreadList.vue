<template>
  <div>Thread</div>
  <div>{{ threadsLoadingState.status }}</div>
  <div
    v-for="thread in threads"
    :key="thread.id"
  >
    {{ thread.name }}
  </div>
</template>

<script setup lang="ts">
import { useThreadStore } from '@core/stores/useThreadStore'

const { threads, threadsLoadingState } = storeToRefs(useThreadStore())
</script>

<style scoped>

</style>
