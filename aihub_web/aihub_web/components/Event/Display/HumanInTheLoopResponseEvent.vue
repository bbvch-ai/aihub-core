<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mdi:robot-confused"
    is-external
  >
    <div class="py-5">
      <ChatMessage
        :message="message"
        :name="event.agent_class"
        :date="new Date(event.event.created_at / 1_000_000)"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type {
  HumanInTheLoopResponseEventReadable, ThreadDto, ChatMessageOutput,
  AgentEventReadable,
} from '@core/sdk/client'

const props = defineProps<{
  event: AgentEventReadable & { event: HumanInTheLoopResponseEventReadable }
  thread: ThreadDto
}>()

const message = computed<ChatMessageOutput>(() => {
  return {
    role: 'user',
    blocks: [
      {
        block_type: 'text',
        text: props.event.event.response,
      },
    ],
  }
})
</script>
