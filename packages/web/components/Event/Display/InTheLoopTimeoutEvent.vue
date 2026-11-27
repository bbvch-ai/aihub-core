<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:clock"
  >
    <p class="pl-6">
      {{ t('event.inTheLoopTimeout.summary', { seconds: event.event.timeout_seconds }) }}
    </p>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type {
  AgentInTheLoopTimeoutEvent,
  BotInTheLoopTimeoutEvent,
  ContextualizedAgentEvent,
  HumanInTheLoopTimeoutEvent,
  ThreadDto,
} from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & {
    event: AgentInTheLoopTimeoutEvent | BotInTheLoopTimeoutEvent | HumanInTheLoopTimeoutEvent
  }
  thread: ThreadDto
}>()

const { t } = useI18n()
</script>
