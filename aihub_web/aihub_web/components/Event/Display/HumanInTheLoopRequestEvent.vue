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
        v-if="isOpen && options.length > 0"
        class="mt-4 flex gap-2"
      >
        <Button
          v-for="option in options"
          :key="option.key"
          :label="option.label"
          severity="secondary"
          @click="submitOption(option.key)"
        />
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

interface HitlOption {
  key: string
  label: string
}

const props = defineProps<{
  event: AgentEventReadable & { event: HumanInTheLoopRequestEventOutputReadable & { options?: HitlOption[] | null } }
  thread: ThreadDto
}>()

const agentIcon = useAgentIconFromThread(props.event, props.thread)
const { runForEvent } = useThreadUtils()
const { sendMessages } = useChatCompletions()

const isOpen = computed<boolean>(() => {
  return runForEvent(props.thread, props.event)?.open_hitl ?? false
})

const options = computed<HitlOption[]>(() => {
  return props.event.event.options ?? []
})

const submitOption = (optionKey: string) => {
  const agent = props.thread.agents?.at(0)
  if (!agent) return

  const agentIdentifier = `${agent.agent_class}/${agent.agent_id}`
  sendMessages({
    model: agentIdentifier,
    messages: [{ role: 'user', content: optionKey }],
    threadId: props.thread.id,
  })
}

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
