<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:file-2"
  >
    <EventDisplayPartFacts :facts="facts" />
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, ReadAttachedFilesEvent, ThreadDto } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: ReadAttachedFilesEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const facts = computed<EventFact[]>(() => [
  { label: t('event.capability.files'), value: (props.event.event.files ?? []).map(file => file.filename) },
  { label: t('event.capability.query'), value: props.event.event.query },
  { label: t('event.capability.reserveTokens'), value: props.event.event.reserve_tokens || null },
  { label: t('event.capability.toolCall'), value: props.event.event.tool_call_id },
])
</script>
