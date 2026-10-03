<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mynaui:tool"
  >
    <div class="flex flex-col gap-6">
      <EventDisplayPartToolCalls
        :messages="event.event.state.messages"
        :tool-call-ids="event.event.tool_call_ids"
      />
      <EventDisplayPartToolLoopState :state="event.event.state" />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, ThreadDto, ToolCallsDecidedEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: ToolCallsDecidedEvent }
  thread: ThreadDto
}>()
</script>
