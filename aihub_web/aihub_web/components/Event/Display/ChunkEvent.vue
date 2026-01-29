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
        :email="event.event.model_name"
        :date="new Date(event.event.created_at / 1_000_000)"
        :icon="agentIcon"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ChatMessageOutput, ChunkEventReadable, ThreadDto, AgentEventReadable } from '@core/sdk/client'

const props = defineProps<{
  event: AgentEventReadable & { event: ChunkEventReadable }
  thread: ThreadDto
}>()

const agentIcon = useAgentIconFromThread(props.event, props.thread)

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
