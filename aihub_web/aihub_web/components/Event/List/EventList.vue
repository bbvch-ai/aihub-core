<template>
  <div class="p-3">
    <Timeline
      :value="events"
      data-key="event_id"
      align="left"
      class="customized-timeline w-full"
    >
      <template #opposite="{ item: event }">
        <div class="flex w-full flex-row justify-end">
          <div class="flex flex-col text-xs text-surface-500 dark:text-surface-400">
            <div>{{ useDateFormat(event.event.created_at / 1_000_000, 'DD.MM.YYYY') }}</div>
            <div>{{ useDateFormat(event.event.created_at / 1_000_000, 'hh:mm:ss') }}</div>
          </div>
        </div>
      </template>
      <template #content="{ item: event }">
        <div class="w-full pb-12">
          <component
            :is="resolveComponentForEvent(event)"
            :event="event"
          />
        </div>
      </template>
      <template #marker>
        <span
          class="z-10 flex size-5 items-center justify-center rounded-full border border-surface-100 bg-white text-white shadow-md shadow-surface-200 dark:border-surface-800 dark:bg-surface-700 dark:shadow-surface-950"
        >
          <Icon
            class="text-green-700"
            name="material-symbols:check"
            size="xs"
          />
        </span>
      </template>
    </Timeline>
  </div>
</template>

<script setup lang="ts">
import type { WsServerEvent } from '@core/sdk/client'

import {
  EventDisplayUserMessageEvent,
  EventDisplayChunkEvent,
  EventDisplayUnknownEvent,
  EventDisplayLLMEvent,
  EventDisplayLLMCostEvent,
  EventDisplayThoughtEvent,
  EventDisplayEmbeddingEvent,
  EventDisplayRerankerEvent,
  EventDisplayRetrieverEvent,
  EventDisplayStopEvent,
  EventDisplayToolEvent,
} from '#components'

defineProps<{
  events: WsServerEvent[]
}>()

const resolveComponentForEvent = (event: WsServerEvent) => {
  const mapping = {
    UserMessageEvent: EventDisplayUserMessageEvent,
    ChunkEvent: EventDisplayChunkEvent,
    LLMEvent: EventDisplayLLMEvent,
    LLMCostEvent: EventDisplayLLMCostEvent,
    ThoughtEvent: EventDisplayThoughtEvent,
    EmbeddingEvent: EventDisplayEmbeddingEvent,
    RerankerEvent: EventDisplayRerankerEvent,
    RetrieverEvent: EventDisplayRetrieverEvent,
    StopEvent: EventDisplayStopEvent,
    ToolEvent: EventDisplayToolEvent,
  }
  const exact_match = mapping[event.event._type]
  if (exact_match) {
    return exact_match
  }
  for (const parent_class in event.event._parent_class_names) {
    const parent_match = mapping[parent_class]
    if (parent_match) {
      return parent_match
    }
  }
  return EventDisplayUnknownEvent
}
</script>

<style scoped>
::v-deep(.customized-timeline) {
  .p-timeline-event-opposite {
    width: 60px;
    max-width: 60px;
  }
}
</style>
