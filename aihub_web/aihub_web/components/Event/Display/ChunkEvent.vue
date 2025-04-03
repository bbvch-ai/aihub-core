<template>
  <EventDisplayBase
    :event="event"
    title="Teilantwort"
    subtitle="Der Assistent hat ein Teil der Antwort generiert und an den Benutzer gesendet, die der Benutzer bereits angezeigt bekommt."
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
