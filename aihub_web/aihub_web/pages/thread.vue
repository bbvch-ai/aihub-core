<template>
  <div>
    <div>
      <div
        v-for="thread in threads"
        :key="thread.id"
      >
        {{ thread.name }}
      </div>
    </div>
    <NuxtPage />
  </div>
</template>

<script lang="ts" setup>
import { useThreadStore } from '@core/stores/useThreadStore'

const { threads } = useThreadStore()
</script>
