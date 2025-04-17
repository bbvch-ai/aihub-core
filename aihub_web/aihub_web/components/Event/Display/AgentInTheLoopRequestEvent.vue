<template>
  <EventDisplayBase
    :event="event"
    icon="mdi:robot-confused"
  >
    <div>
      Delegiere an: {{ event.event.other_agent_topic.agent_class }}
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { AgentInTheLoopRequestEvent, WsServerEvent } from '@core/sdk/client'

defineProps<{
  event: WsServerEvent & { event: AgentInTheLoopRequestEvent }
}>()
</script>

<style scoped>

</style>
