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
].filter(Boolean).join(' · ') || t('event.extraction.everyDocument')))

// The bounds are calendar days: read as text, never through the local time zone, which can shift them by a day.
const day = (bound: Date | string | null | undefined): string => {
  if (!bound) return '…'
  return bound instanceof Date ? bound.toISOString().slice(0, 10) : bound
}

const pathDates = computed<string | null>(() => {
  const range = props.event.event.selection?.path_date_range
  return range ? `${day(range.start)} – ${day(range.end)}` : null
})

const facts = computed<EventFact[]>(() => [
  {
    label: t('event.extraction.confirmed'),
    value: props.event.event.confirmed ? t('event.parts.yes') : null,
  },
  { label: t('event.extraction.fields'), value: props.event.event.fields || null },
  { label: t('event.extraction.instructions'), value: props.event.event.instructions },
  { label: t('event.extraction.documentCondition'), value: props.event.event.document_condition },
  { label: t('event.extraction.pathDates'), value: pathDates.value },
  { label: t('event.extraction.criteria'), value: criteria.value },
  {
    label: t('event.extraction.collections'),
    value: (props.event.event.collections ?? []).map(collection => `${collection.bucket_name} / ${collection.namespace_name}`),
  },
  { label: t('event.extraction.notices'), value: props.event.event.notices },
  { label: t('event.capability.toolCall'), value: props.event.event.tool_call_id },
])
</script>
