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
import type { ExceptionEvent, ThreadDto, WsServerEventReadable } from '@core/sdk/client'

defineProps<{
  event: WsServerEventReadable & { event: ExceptionEvent }
  thread: ThreadDto
}>()
</script>
