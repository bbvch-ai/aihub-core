<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mdi:robot-confused"
    :is-warning="isOpen"
  >
    <div class="py-5">
      <ChatMessage
        :message="message"
        :name="event.agent_class"
        :preferred-username="event.agent_id"
        :date="new Date(event.event.created_at / 1_000_000)"
        :icon="agentIcon"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type {
  ChatMessage,
  HumanInTheLoopRequestEventReadable,
  ThreadDto,
  AgentEventReadable,
} from '@core/sdk/client'

const props = defineProps<{
  event: AgentEventReadable & { event: HumanInTheLoopRequestEventReadable }
  thread: ThreadDto
}>()

const agentIcon = useAgentIconFromThread(props.event, props.thread)
const { runForEvent } = useThreadUtils()

const isOpen = computed<boolean>(() => {
  return runForEvent(props.thread, props.event)?.open_hitl ?? false
})

const message = computed<ChatMessage>(() => {
  return {
    role: 'assistant',
    agent_class: props.event.agent_class,
    agent_id: props.event.agent_id,
    blocks: [
      {
        block_type: 'text',
        text: props.event.event.question,
      },
    ],
  }
})
</script>
