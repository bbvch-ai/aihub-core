<template>
  <EventDisplayBase
    :event="event"
    title="Delegation an anderen Agenten"
    icon="mdi:robot-confused"
    subtitle="Der Assistent hat eine Anfrage an einen anderen Agenten oder Assistenten weitergeleitet"
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
