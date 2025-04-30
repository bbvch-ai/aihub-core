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
        :date="new Date(event.event.created_at / 1_000_000)"
        :icon="agentIcon"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import useAgentIconFromThread from '@core/composables/useAgentIconFromThread'

import type {
  AssistantChatMessageOutput,
  HumanInTheLoopRequestEvent,
  ThreadDto,
  WsServerEvent,
} from '@core/sdk/client'

const props = defineProps<{
  event: WsServerEvent & { event: HumanInTheLoopRequestEvent }
  thread: ThreadDto
}>()

const agentIcon = useAgentIconFromThread(props.event, props.thread)

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
