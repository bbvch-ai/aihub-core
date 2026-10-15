<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mdi:web-check"
  >
    <div class="flex flex-col gap-4">
      <EventDisplayPartFacts :facts="facts" />
      <ChatSourceNodes :nodes="event.event.grounding_nodes ?? []" />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, ThreadDto, WebFetchFailureReason, WebPagesFetchedEvent } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: WebPagesFetchedEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const failureReason = (reason: WebFetchFailureReason) => t(`event.capability.webFetchFailure.${reason}`)

const facts = computed<EventFact[]>(() => [
  { label: t('event.capability.pagesRead'), value: (props.event.event.grounding_nodes ?? []).length },
  {
    label: t('event.capability.notRead'),
    value: (props.event.event.failures ?? []).map(failure => `${failure.url}: ${failureReason(failure.reason)}`),
  },
  { label: t('event.capability.toolCall'), value: props.event.event.tool_call_id },
])
</script>
