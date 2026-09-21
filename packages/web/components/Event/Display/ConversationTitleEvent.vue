<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mdi:format-title"
  >
    <p class="font-medium text-surface-700 dark:text-surface-200">
      {{ event.event.title }}
    </p>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ConversationTitleEvent, ThreadDto, ContextualizedAgentEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: ConversationTitleEvent }
  thread: ThreadDto
}>()
</script>
