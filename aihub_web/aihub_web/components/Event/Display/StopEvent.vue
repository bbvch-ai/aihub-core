<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="icon-park-twotone:success"
  />
</template>

<script setup lang="ts">
import type { StopEvent, ThreadResponse, WsServerEvent } from '@core/sdk/client'

defineProps<{
  event: WsServerEvent & { event: StopEvent }
  thread: ThreadResponse
}>()
</script>

<style scoped>

</style>
