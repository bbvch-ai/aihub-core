<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:note"
  >
    <div class="py-5">
      <ChatMessage
        :message="message"
        :name="`${event.agent_class}/${event.agent_id}`"
        :email="event.event.model_name"
        :date="new Date(event.event.created_at / 1_000_000)"
        :icon="agentIcon"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ChatMessage, ChunkEvent, ThreadDto, ContextualizedAgentEvent } from '@core/sdk/client'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: ChunkEvent }
  thread: ThreadDto
}>()

const agentIcon = useAgentIconFromThread(props.event, props.thread)

const message = computed<ChatMessage>(() => {
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
