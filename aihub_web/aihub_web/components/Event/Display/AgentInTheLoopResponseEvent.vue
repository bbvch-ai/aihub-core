<template>
  <EventDisplayBase
    :event="event"
    icon="mdi:robot-happy"
  >
    {{ event.event }}
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { AgentInTheLoopResponseEvent, WsServerEvent } from '@core/sdk/client'

defineProps<{
  event: WsServerEvent & { event: AgentInTheLoopResponseEvent }
}>()
</script>

<style scoped>

</style>
