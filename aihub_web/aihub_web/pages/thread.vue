<template>
  <div>
    <ThreadList />
    <NuxtPage />
  </div>
</template>

<script lang="ts" setup>
import { useThreadStore } from '@core/stores/useThreadStore'

const { threads } = useThreadStore()
</script>
