<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:file"
  >
    <div class="flex flex-col gap-4">
      <ChatSourceNodes
        :nodes="event.event.nodes ?? []"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { RetrieverEvent, ThreadDto, ContextualizedAgentEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: RetrieverEvent }
  thread: ThreadDto
}>()
</script>
