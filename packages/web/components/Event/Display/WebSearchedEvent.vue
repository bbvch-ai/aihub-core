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
import type { ContextualizedAgentEvent, ThreadDto, WebSearchedEvent } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: WebSearchedEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const results = computed(() => props.event.event.results ?? [])

const facts = computed<EventFact[]>(() => [
  { label: t('event.capability.searchQueries'), value: props.event.event.queries ?? [] },
  { label: t('event.capability.sitesFound'), value: results.value.map(result => result.url) },
  { label: t('event.capability.pagesRead'), value: results.value.filter(result => result.read).length },
  { label: t('event.capability.unresponsiveEngines'), value: props.event.event.unresponsive_engines ?? [] },
  { label: t('event.capability.toolCall'), value: props.event.event.tool_call_id },
])
</script>
