<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="line-md:text-box"
  >
    <div class="py-5">
      <ChatMessage
        :message="message"
        :name="`${event.agent_class}/${event.agent_id}`"
        :preferred-username="event.event.model_name"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ChatMessageOutput, ChunkEvent, ThreadResponse, WsServerEvent } from '@core/sdk/client'

const props = defineProps<{
  event: WsServerEvent & { event: ChunkEvent }
  thread: ThreadResponse
}>()

const message = computed<ChatMessageOutput>(() => {
  return {
    role: 'assistant',
    blocks: [
      {
        block_type: 'text',
        text: props.event.event.content,
      },
    ],
  }
})
</script>
