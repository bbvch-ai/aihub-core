<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="line-md:document-twotone"
  >
    <div class="flex flex-col gap-4">
      <ChatSourceNodes
        :nodes="event.event.nodes ?? []"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { RetrieverEvent, ThreadDto, AgentEventReadable } from '@core/sdk/client'

defineProps<{
  event: AgentEventReadable & { event: RetrieverEvent }
  thread: ThreadDto
}>()
</script>
