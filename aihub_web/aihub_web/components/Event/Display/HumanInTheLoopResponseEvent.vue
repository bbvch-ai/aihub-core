<template>
  <EventDisplayBase
    :event="event"
    title="Rückfrage beantwortet"
    icon="mdi:robot-confused"
    subtitle="Der Benutzer hat die Rückfrage beantwortet"
  >
    <div class="py-5">
      <ChatMessage
        :message="message"
        :name="event.agent_class"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type {
  HumanInTheLoopResponseEvent, UserChatMessageInput,
  WsServerEvent,
} from '@core/sdk/client'

const props = defineProps<{
  event: WsServerEvent & { event: HumanInTheLoopResponseEvent }
}>()

const message = computed<UserChatMessageInput>(() => {
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

<style scoped>

</style>
