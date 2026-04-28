<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="icon-park-twotone:success"
    :is-warning="!event.event.context_sufficient"
  >
    <Message
      v-if="!event.event.context_sufficient"
      severity="warn"
      icon="pi pi-exclamation-triangle"
      variant="simple"
      size="small"
    >
      {{ t('event.rag_stop.context_insufficient') }}
    </Message>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ThreadDto, RagStopEvent, ContextualizedAgentEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: RagStopEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()
</script>
