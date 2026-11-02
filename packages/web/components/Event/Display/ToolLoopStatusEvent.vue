<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mynaui:tool"
  >
    <div class="flex items-center gap-2 text-sm">
      <Icon
        :name="event.event.done ? 'mage:check-circle' : 'mage:loading'"
        class="size-4"
      />
      <span>{{ event.event.description }}</span>
      <span class="text-xs text-surface-500 dark:text-surface-400">{{ t('event.toolLoop.loop') }}: {{ event.event.loop }}</span>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, ThreadDto, ToolLoopStatusEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: ToolLoopStatusEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()
</script>
