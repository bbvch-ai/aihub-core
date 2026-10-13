<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:file-2"
  >
    <EventDisplayPartMessageList
      :messages="event.event.block ?? []"
      :event="event"
      :thread="thread"
    />
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { AttachedFilesReadEvent, ContextualizedAgentEvent, ThreadDto } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: AttachedFilesReadEvent }
  thread: ThreadDto
}>()
</script>
