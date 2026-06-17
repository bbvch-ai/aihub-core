<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mdi:comment-question-outline"
  >
    <ul class="flex flex-col gap-1">
      <li
        v-for="question in event.event.questions"
        :key="question"
        class="text-sm text-surface-600 dark:text-surface-400"
      >
        {{ question }}
      </li>
    </ul>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { SuggestedFollowUpQuestionsEvent, ThreadDto, ContextualizedAgentEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: SuggestedFollowUpQuestionsEvent }
  thread: ThreadDto
}>()
</script>
