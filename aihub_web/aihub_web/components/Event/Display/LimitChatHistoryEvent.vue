<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="material-symbols:history"
  >
    <div class="flex flex-col gap-8">
      <div class="flex items-center gap-2 text-sm text-surface-600 dark:text-surface-400">
        <Icon
          name="material-symbols:history"
          class="size-4"
        />
        <span>{{ t('event.limitChatHistory.summary', { count: event.event.limited_history.length }) }}</span>
      </div>

      <div
        v-for="(message, index) in event.event.limited_history"
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
  LimitChatHistoryEventReadable,
  ThreadDto,
  AgentEventReadable,
} from '@core/sdk/client'

const props = defineProps<{
  event: AgentEventReadable & { event: LimitChatHistoryEventReadable }
  thread: ThreadDto
}>()

const { t } = useI18n()
const agentIcon = useAgentIconFromThread(props.event, props.thread)

const getMessageName = (role: string) => {
  switch (role) {
    case 'user':
      return t('event.limitChatHistory.user')
    case 'system':
      return t('event.limitChatHistory.system')
    case 'assistant':
      return t('event.limitChatHistory.assistant')
    default:
      return t('event.limitChatHistory.assistant')
  }
}
</script>
