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
      <div
        v-if="previewNote || event.event.file"
        class="flex flex-wrap items-center gap-3"
      >
        <span
          v-if="previewNote"
          class="text-sm text-surface-500 dark:text-surface-400"
        >
          {{ previewNote }}
        </span>
        <Button
          v-if="event.event.file"
          :label="t('event.extraction.download')"
          :loading="downloading"
          icon="pi pi-download"
          severity="secondary"
          size="small"
          @click="download"
        />
      </div>
      <MarkdownRenderer :md="event.event.summary" />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import { getExtractedTableDownloadUrl } from '@core/sdk/client'

import type { ContextualizedAgentEvent, RecordsExtractedEvent, ThreadDto } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: RecordsExtractedEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()
const toast = useToast()
const { tenantId } = useTenant()

const downloading = ref(false)

const rowCount = computed<number>(() => props.event.event.row_count ?? 0)
const totalRowCount = computed<number>(() => props.event.event.total_row_count ?? 0)

const previewNote = computed<string | null>(() => rowCount.value < totalRowCount.value
  ? t('event.extraction.previewRows', { shown: rowCount.value, total: totalRowCount.value })
  : null)

const facts = computed<EventFact[]>(() => [
  { label: t('event.extraction.files'), value: props.event.event.file_count },
  { label: t('event.extraction.failedFiles'), value: props.event.event.failed_count },
  { label: t('event.extraction.rows'), value: `${rowCount.value} / ${totalRowCount.value}` },
  { label: t('event.extraction.truncated'), value: t(props.event.event.truncated ? 'event.parts.yes' : 'event.parts.no') },
  {
    label: t('event.extraction.awaitingConfirmation'),
    value: props.event.event.awaiting_confirmation ? t('event.parts.yes') : null,
  },
  { label: t('event.capability.toolCall'), value: props.event.event.tool_call_id },
])

// The file is attached as a download, so navigating to it saves it without leaving the page; a window opened after
// the request would be blocked as a popup.
const download = async () => {
  downloading.value = true
  try {
    const { url } = await getExtractedTableDownloadUrl({
      composable: '$fetch',
      path: { tenant_id: tenantId.value!, thread_id: props.thread.id, extraction_id: props.event.event.extraction_id },
    })
    window.location.assign(url)
  }
  catch (error) {
    const detail = (error as { data?: { detail?: string } })?.data?.detail
    toast.add({ severity: 'error', summary: t('event.extraction.downloadFailed'), detail, life: 5000 })
  }
  finally {
    downloading.value = false
  }
}
</script>
