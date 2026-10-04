<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:robot-sad"
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
  HumanInTheLoopResponseEvent, ThreadDto, ChatMessage,
  ContextualizedAgentEvent,
} from '@core/sdk/client'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: HumanInTheLoopResponseEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()

const responseText = computed<string>(() => {
  const response = props.event.event.response
  if (typeof response === 'boolean') {
    return t(`event.humanInTheLoopResponse.${response ? 'confirmed' : 'declined'}`)
  }
  return response
})

const message = computed<ChatMessage>(() => {
  return {
    role: 'user',
    blocks: [
      {
        block_type: 'text',
        text: responseText.value,
      },
    ],
  }
})
</script>
