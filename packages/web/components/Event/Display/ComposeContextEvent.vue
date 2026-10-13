<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mdi:database-plus"
  >
    <div class="flex flex-col gap-6">
      <EventDisplayPartFacts :facts="facts" />
      <EventDisplayPartMessageList
        v-for="(block, index) in blocks"
        :key="index"
        :messages="block"
        :event="event"
        :thread="thread"
        :title="t('event.capability.block', { number: index + 1 })"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ComposeContextEvent, ContextualizedAgentEvent, ThreadDto } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: ComposeContextEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const blocks = computed(() => (props.event.event.blocks ?? []).filter(block => block.length > 0))

const facts = computed<EventFact[]>(() => [
  { label: t('event.capability.historyMessages'), value: props.event.event.history.length },
  { label: t('event.capability.blocks'), value: blocks.value.length },
])
</script>
