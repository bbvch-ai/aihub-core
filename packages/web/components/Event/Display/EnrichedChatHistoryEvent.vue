<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="lucide:layers"
  >
    <div class="flex flex-col gap-8">
      <div class="flex items-center gap-2 text-sm text-surface-600 dark:text-surface-400">
        <Icon
          name="lucide:layers"
          class="size-4"
        />
        <span>{{ t('event.enrichedChatHistory.summary', { count: event.event.extended_history.length }) }}</span>
      </div>

      <div
        v-for="(message, index) in event.event.extended_history"
        :key="index"
        class="flex flex-col gap-2"
      >
        <ChatMessage
          :message="message"
          :name="getMessageName(message.role)"
          :email="''"
          :date="new Date(event.event.created_at / 1_000_000)"
          :icon="agentIcon"
        />
      </div>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type {
  EnrichedChatHistoryEvent,
  ThreadDto,
  AgentEventReadable,
} from '@core/sdk/client'

const props = defineProps<{
  event: AgentEventReadable & { event: EnrichedChatHistoryEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()
const agentIcon = useAgentIconFromThread(props.event, props.thread)

const getMessageName = (role: string) => {
  switch (role) {
    case 'user':
      return t('event.enrichedChatHistory.user')
    case 'system':
      return t('event.enrichedChatHistory.system')
    case 'assistant':
      return t('event.enrichedChatHistory.assistant')
    default:
      return t('event.enrichedChatHistory.assistant')
  }
}
</script>
