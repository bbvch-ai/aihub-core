<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mdi:table-search"
  >
    <EventDisplayPartFacts :facts="facts" />
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, ExtractRecordsEvent, ThreadDto } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: ExtractRecordsEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const criteria = computed<string[]>(() => (props.event.event.selection?.any_of ?? []).map(criterion => [
  criterion.path_glob,
  criterion.path_regex && `/${criterion.path_regex}/`,
  criterion.content_query && `"${criterion.content_query}"`,
  (criterion.document_ids ?? []).length ? t('event.extraction.documentIds', { count: (criterion.document_ids ?? []).length }) : null,
].filter(Boolean).join(' · ')))

const facts = computed<EventFact[]>(() => [
  {
    label: t('event.extraction.continuePending'),
    value: props.event.event.continue_pending ? t('event.parts.yes') : null,
  },
  { label: t('event.extraction.fields'), value: props.event.event.fields || null },
  { label: t('event.extraction.instructions'), value: props.event.event.instructions },
  { label: t('event.extraction.criteria'), value: criteria.value },
  {
    label: t('event.extraction.collections'),
    value: (props.event.event.collections ?? []).map(collection => `${collection.bucket_name} / ${collection.namespace_name}`),
  },
  { label: t('event.extraction.notices'), value: props.event.event.notices },
  { label: t('event.capability.toolCall'), value: props.event.event.tool_call_id },
])
</script>
