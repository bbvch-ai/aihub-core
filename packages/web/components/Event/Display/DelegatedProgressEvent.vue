<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:robot"
  >
    <p class="pl-6">
      {{ t('event.delegatedProgress.summary', { agent: `${event.event.agent_class}/${event.event.agent_id}`, step: event.event.step }) }}
    </p>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, DelegatedProgressEvent, ThreadDto } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: DelegatedProgressEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()
</script>
