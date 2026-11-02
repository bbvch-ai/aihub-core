<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:stop-circle-fill"
  >
    <div class="flex flex-col gap-4">
      <EventDisplayPartFacts :facts="facts" />
      <p
        v-if="answer"
        class="whitespace-pre-wrap rounded-xl bg-surface-50 p-3 text-sm dark:bg-surface-850"
      >
        {{ answer }}
      </p>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { CompleteConversationEvent, ContextualizedAgentEvent, ThreadDto } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: CompleteConversationEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const answer = computed(() => props.event.event.answer.output_messages?.at(-1)?.content)

const facts = computed<EventFact[]>(() => [
  { label: t('event.capability.stop'), value: props.event.event.stop?._event_name ?? 'LLMStopEvent' },
])
</script>
