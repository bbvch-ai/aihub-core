<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mynaui:tool"
  >
    <div class="flex flex-col gap-4">
      <EventDisplayPartFacts :facts="facts" />
      <Tag
        v-if="event.event.stopped_early"
        :value="t('event.toolLoop.stoppedEarly')"
        severity="warn"
        class="self-start"
      />
      <p
        v-if="answer"
        class="whitespace-pre-wrap rounded-xl bg-surface-50 p-3 text-sm dark:bg-surface-850"
      >
        {{ answer }}
      </p>
      <EventDisplayPartMessageList
        v-if="(event.event.block ?? []).length > 0"
        :messages="event.event.block ?? []"
        :event="event"
        :thread="thread"
        :title="t('event.toolLoop.gathered')"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, ThreadDto, ToolLoopFinishedEvent } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: ToolLoopFinishedEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const answer = computed(() => props.event.event.answer?.output_messages?.at(-1)?.content)

const facts = computed<EventFact[]>(() => [
  { label: t('event.toolLoop.loop'), value: props.event.event.loop },
  { label: t('event.toolLoop.gatheredMessages'), value: (props.event.event.block ?? []).length || null },
])
</script>
