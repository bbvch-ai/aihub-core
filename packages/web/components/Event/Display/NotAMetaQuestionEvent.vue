<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mdi:help-circle-outline"
  >
    <span class="text-sm text-surface-600 dark:text-surface-400">
      {{ event.event.reasoning }}
    </span>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, NotAMetaQuestionEvent, ThreadDto } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: NotAMetaQuestionEvent }
  thread: ThreadDto
}>()
</script>
