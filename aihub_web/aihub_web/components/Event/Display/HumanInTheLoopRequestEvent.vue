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
      <div
        v-if="isOpen && isConfirmation"
        class="mt-4 flex gap-2"
      >
        <span class="text-sm text-surface-500">
          {{ t('event.hitl.confirmationHint') }}
        </span>
      </div>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type {
  ChatMessageOutput,
  HumanInTheLoopRequestEventOutputReadable,
  ThreadDto,
  AgentEventReadable,
} from '@core/sdk/client'

const props = defineProps<{
  event: AgentEventReadable & { event: HumanInTheLoopRequestEventOutputReadable }
  thread: ThreadDto
}>()

const { t } = useI18n()
const agentIcon = useAgentIconFromThread(props.event, props.thread)
const { runForEvent } = useThreadUtils()

const isOpen = computed<boolean>(() => {
  return runForEvent(props.thread, props.event)?.open_hitl ?? false
})

const isConfirmation = computed<boolean>(() => {
  return props.event.event.hitl_type === 'confirmation'
})

const message = computed<ChatMessageOutput>(() => {
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
