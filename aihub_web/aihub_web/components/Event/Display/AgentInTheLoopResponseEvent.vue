<template>
  <EventDisplayBase
    :event="event"
    title="Erledigte Delegation des anderen Agenten"
    icon="mdi:robot-happy"
    subtitle="Der involvierte Assistent hat die Anfrage bearbeitet"
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
