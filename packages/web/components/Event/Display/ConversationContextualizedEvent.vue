<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:edit"
  >
    <div class="flex flex-col gap-4">
      <EventDisplayPartFacts :facts="facts" />
      <Tag
        v-if="event.event.condensed"
        :value="t('event.capability.condensed')"
        severity="info"
        class="self-start"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, ConversationContextualizedEvent, ThreadDto } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: ConversationContextualizedEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const facts = computed<EventFact[]>(() => [
  { label: t('event.capability.query'), value: props.event.event.query },
  { label: t('event.capability.historyMessages'), value: props.event.event.history.length },
])
</script>
