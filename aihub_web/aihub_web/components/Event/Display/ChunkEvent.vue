<template>
  <EventDisplayBase
    :event="props.event"
    title="Chunk"
    subtitle="Message sent from the Assistant to the User"
  >
    <div class="py-5">
      <ChatMessage
        :message="message"
        :name="`${props.event.agent_class}/${props.event.agent_id}`"
        :preferred-username="props.event.event.model_name"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ChatMessageOutput, ChunkEvent, WsServerEvent } from '@core/sdk/client'

const props = defineProps<{
  event: WsServerEvent & { event: ChunkEvent }
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
