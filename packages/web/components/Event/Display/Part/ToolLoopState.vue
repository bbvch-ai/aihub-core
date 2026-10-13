<template>
  <EventDisplayPartFacts :facts="facts" />
</template>

<script setup lang="ts">
import type { ToolLoopState } from '@core/sdk/client'
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  state: ToolLoopState
}>()

const { t } = useI18n()

const facts = computed<EventFact[]>(() => [
  { label: t('event.toolLoop.loop'), value: props.state.loop },
  { label: t('event.toolLoop.mode'), value: t(`event.toolLoop.modes.${props.state.mode}`) },
  {
    label: t('event.toolLoop.iteration'),
    value: props.state.max_iterations
      ? `${props.state.iteration ?? 0} / ${props.state.max_iterations}`
      : props.state.iteration ?? 0,
  },
  { label: t('event.toolLoop.toolCallsMade'), value: props.state.tool_calls_made ?? 0 },
  { label: t('event.toolLoop.messages'), value: props.state.messages.length },
  { label: t('event.toolLoop.offeredTools'), value: (props.state.tools ?? []).map(tool => tool.name) },
  {
    label: t('event.toolLoop.condensedResults'),
    value: props.state.condensed_tool_call_ids?.length || null,
  },
  {
    label: t('event.toolLoop.needsCondensing'),
    value: props.state.needs_condensing ? t('event.parts.yes') : null,
  },
])
</script>
