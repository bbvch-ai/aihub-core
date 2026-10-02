<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mynaui:tool"
  >
    <div class="flex flex-col gap-4">
      <div class="flex items-center gap-2">
        <span class="font-semibold">{{ event.event.name }}</span>
        <Tag
          v-if="event.event.is_error"
          :value="t('event.toolLoop.failed')"
          severity="danger"
        />
        <span class="text-xs text-surface-500 dark:text-surface-400">{{ event.event.tool_call_id }}</span>
      </div>
      <pre class="max-h-96 overflow-auto whitespace-pre-wrap break-words rounded-xl bg-surface-50 p-3 text-xs dark:bg-surface-850">{{ event.event.content }}</pre>
      <EventDisplayPartMessageList
        v-if="(event.event.block ?? []).length > 0"
        :messages="event.event.block ?? []"
        :event="event"
        :thread="thread"
        :title="t('event.toolLoop.resultContext')"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, ThreadDto, ToolResultEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: ToolResultEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()
</script>
