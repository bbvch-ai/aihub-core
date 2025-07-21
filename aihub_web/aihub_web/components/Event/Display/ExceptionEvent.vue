<template>
  <EventDisplayBase
    is-error
    :event="event"
    :thread="thread"
    icon="mingcute:thought-fill"
  >
    <p class="pl-6 font-bold">
      {{ event.event.message }}
    </p>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ExceptionEvent, ThreadDto, WsServerAgentEventReadable } from '@core/sdk/client'

defineProps<{
  event: WsServerAgentEventReadable & { event: ExceptionEvent }
  thread: ThreadDto
}>()
</script>
