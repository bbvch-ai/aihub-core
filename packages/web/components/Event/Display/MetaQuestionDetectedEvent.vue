<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mdi:help-circle-outline"
  >
    <div class="flex flex-col gap-2">
      <Tag
        :value="t(`event.metaQuestionDetected.category.${event.event.category}`)"
        severity="info"
        class="self-start"
      />
      <span class="text-sm text-surface-600 dark:text-surface-400">
        {{ event.event.reasoning }}
      </span>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { MetaQuestionDetectedEvent, ThreadDto, ContextualizedAgentEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: MetaQuestionDetectedEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()
</script>
