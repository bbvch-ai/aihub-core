<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:clock"
  >
    <div class="flex flex-col gap-8">
      <div class="flex items-center gap-2 text-sm text-surface-600 dark:text-surface-400">
        <Icon
          name="mage:clock"
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
  LimitChatHistoryEvent,
  ThreadDto,
  ContextualizedAgentEvent,
} from '@core/sdk/client'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: LimitChatHistoryEvent }
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
