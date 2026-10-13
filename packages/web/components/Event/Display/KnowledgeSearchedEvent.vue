<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:file"
  >
    <div class="flex flex-col gap-4">
      <EventDisplayPartFacts :facts="facts" />
      <ChatSourceNodes :nodes="event.event.grounding_nodes ?? []" />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, KnowledgeSearchedEvent, ThreadDto } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: KnowledgeSearchedEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const facts = computed<EventFact[]>(() => [
  { label: t('event.capability.sections'), value: (props.event.event.grounding_nodes ?? []).length },
  {
    label: t('event.capability.notSearched'),
    value: (props.event.event.refused ?? []).map(reference => `${reference.database} / ${reference.namespace}`),
  },
  { label: t('event.capability.toolCall'), value: props.event.event.tool_call_id },
])
</script>
