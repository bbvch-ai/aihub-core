<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mingcute:thought-fill"
  >
    <p class="border-l-4 border-surface-200 pl-3 italic dark:border-surface-600">
      {{ event.event.reasoning_content }}
    </p>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ThoughtEvent, ThreadDto, ContextualizedAgentEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: ThoughtEvent }
  thread: ThreadDto
}>()
</script>
