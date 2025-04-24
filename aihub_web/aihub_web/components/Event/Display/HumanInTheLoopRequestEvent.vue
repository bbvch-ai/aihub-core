<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mdi:robot-confused"
  >
    <div class="py-5">
      <ChatMessage
        :message="message"
        :name="event.agent_class"
        :preferred-username="event.agent_id"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type {
  AssistantChatMessageOutput,
  HumanInTheLoopRequestEvent,
  ThreadResponse,
  WsServerEvent,
} from '@core/sdk/client'

const props = defineProps<{
  event: WsServerEvent & { event: HumanInTheLoopRequestEvent }
  thread: ThreadResponse
}>()

const message = computed<AssistantChatMessageOutput>(() => {
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

<style scoped>

</style>
