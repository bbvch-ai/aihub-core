<template>
  <div>Thread --- {{ activeThreadId }}</div>
  <div>{{ threadsLoadingState.status }}</div>
  <div
    v-for="thread in threads"
    :key="thread.id"
  >
    {{ thread.name }}
  </div>
  <Listbox
    v-model="activeThreadId"
    :options="threads"
    option-label="name"
    option-value="id"
  />
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useThreadStore } from '@core/stores/useThreadStore'
import { useActiveThread } from '@core/composables/useActiveThread'

const { threads, threadsLoadingState } = storeToRefs(useThreadStore())
const { activeThreadId } = useActiveThread()
</script>

<style scoped>

</style>
