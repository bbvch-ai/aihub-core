<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mdi:tag-multiple"
  >
    <div class="flex flex-wrap gap-2">
      <Tag
        v-for="tag in event.event.tags"
        :key="tag"
        :value="tag"
        severity="info"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ConversationTagsEvent, ThreadDto, ContextualizedAgentEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: ConversationTagsEvent }
  thread: ThreadDto
}>()
</script>
