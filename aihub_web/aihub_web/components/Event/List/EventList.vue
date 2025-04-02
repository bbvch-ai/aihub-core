<template>
  <div class="flex flex-col gap-8 p-3">
    <component
      :is="resolveComponentForEvent(event.event._type)"
      v-for="event in props.events"
      :key="event.event_id"
      :event="event"
    />
  </div>
</template>

<script setup lang="ts">
import type { WsServerEvent } from '@core/sdk/client'

import {
  EventDisplayUserMessageEvent,
  EventDisplayChunkEvent,
  EventDisplayUnknownEvent,
  EventDisplayLLMStopEvent,
  EventDisplayLLMCostEvent,
} from '#components'

const props = defineProps<{
  events: WsServerEvent[]
}>()

const resolveComponentForEvent = (eventType: string) => {
  return {
    UserMessageEvent: EventDisplayUserMessageEvent,
    ChunkEvent: EventDisplayChunkEvent,
    LLMStopEvent: EventDisplayLLMStopEvent,
    LLMCostEvent: EventDisplayLLMCostEvent,
  }[eventType] || EventDisplayUnknownEvent
}
</script>

<style scoped>

</style>
