<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mdi:table-large"
  >
    <div class="flex flex-col gap-4">
      <EventDisplayPartFacts :facts="facts" />
      <MarkdownRenderer
        v-if="event.event.table"
        class="overflow-x-auto"
        :md="event.event.table"
      />
      <MarkdownRenderer :md="event.event.summary" />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, RecordsExtractedEvent, ThreadDto } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: RecordsExtractedEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const facts = computed<EventFact[]>(() => [
  { label: t('event.extraction.files'), value: props.event.event.file_count },
  { label: t('event.extraction.failedFiles'), value: props.event.event.failed_count },
  { label: t('event.extraction.rows'), value: `${props.event.event.row_count} / ${props.event.event.total_row_count}` },
  { label: t('event.extraction.truncated'), value: t(props.event.event.truncated ? 'event.parts.yes' : 'event.parts.no') },
  { label: t('event.extraction.remainingDocuments'), value: props.event.event.remaining_documents || null },
  { label: t('event.extraction.remainingRows'), value: props.event.event.remaining_rows || null },
  { label: t('event.capability.toolCall'), value: props.event.event.tool_call_id },
])
</script>
