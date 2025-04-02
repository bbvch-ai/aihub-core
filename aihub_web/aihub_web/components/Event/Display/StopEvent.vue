<template>
  <EventDisplayBase
    :event="props.event"
    title="Stop"
    subtitle="Internal thought of the agent"
  >
    StopEvent
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { StopEvent, WsServerEvent } from '@core/sdk/client'

const props = defineProps<{
  event: WsServerEvent & { event: StopEvent }
}>()
</script>

<style scoped>

</style>
