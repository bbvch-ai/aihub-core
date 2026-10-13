<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:file-2"
  >
    <div class="flex flex-col gap-4">
      <div class="flex items-center gap-2">
        <span class="font-semibold">{{ event.event.filename }}</span>
        <Tag
          :value="t(`event.capability.fileStatus.${event.event.status}`)"
          :severity="severity"
        />
      </div>
      <EventDisplayPartFacts :facts="facts" />
      <pre
        v-if="event.event.content"
        class="max-h-96 overflow-auto whitespace-pre-wrap break-words rounded-xl bg-surface-50 p-3 text-xs dark:bg-surface-850"
      >{{ event.event.content }}</pre>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { AttachedFileEvent, ContextualizedAgentEvent, ThreadDto } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: AttachedFileEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const severity = computed(() => ({ read: 'success', truncated: 'warn', failed: 'danger' })[props.event.event.status])

const facts = computed<EventFact[]>(() => [
  { label: t('event.capability.citationId'), value: props.event.event.citation_id },
  { label: t('event.capability.pages'), value: props.event.event.number_of_pages },
  { label: t('event.capability.error'), value: props.event.event.error },
])
</script>
