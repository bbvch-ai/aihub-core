<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="lucide:brain-circuit"
  >
    <div class="flex flex-col gap-8">
      <div class="flex items-center gap-2 text-sm text-surface-600 dark:text-surface-400">
        <Icon
          name="lucide:brain-circuit"
          class="size-4"
        />
        <span>{{ t('event.addMemoryToChatHistory.summary', { count: event.event.extended_history.length }) }}</span>
      </div>

      <div
        v-for="(message, index) in event.event.extended_history"
        :key="index"
        class="flex flex-col gap-2"
      >
        <ChatMessage
          :message="message"
          :name="getMessageName(message.role)"
          :preferred-username="''"
          :date="new Date(event.event.created_at / 1_000_000)"
          :icon="agentIcon"
        />
      </div>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type {
  AddMemoryToChatHistoryEventReadable,
  ThreadDto,
  AgentEventReadable,
} from '@core/sdk/client'

const props = defineProps<{
  event: AgentEventReadable & { event: AddMemoryToChatHistoryEventReadable }
  thread: ThreadDto
}>()

const { t } = useI18n()
const agentIcon = useAgentIconFromThread(props.event, props.thread)

const getMessageName = (role: string) => {
  switch (role) {
    case 'user':
      return t('event.addMemoryToChatHistory.user')
    case 'system':
      return t('event.addMemoryToChatHistory.system')
    case 'assistant':
      return t('event.addMemoryToChatHistory.assistant')
    default:
      return t('event.addMemoryToChatHistory.assistant')
  }
}
</script>
