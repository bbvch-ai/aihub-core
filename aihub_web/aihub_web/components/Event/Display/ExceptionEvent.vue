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
import type { ExceptionEventReadable, ThreadDto, AgentEventReadable } from '@core/sdk/client'

defineProps<{
  event: AgentEventReadable & { event: ExceptionEventReadable }
  thread: ThreadDto
}>()
</script>
