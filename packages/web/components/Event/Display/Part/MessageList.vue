<template>
  <div class="flex flex-col gap-4">
    <p
      v-if="title"
      class="text-sm font-semibold text-surface-600 dark:text-surface-400"
    >
      {{ title }}
    </p>
    <p
      v-if="messages.length === 0"
      class="text-sm text-surface-500 dark:text-surface-400"
    >
      {{ t('event.parts.noMessages') }}
    </p>
    <ChatMessage
      v-for="(message, index) in messages"
      :key="index"
      :message="message"
      :name="roleName(message.role)"
      :email="''"
      :date="new Date(event.event.created_at / 1_000_000)"
      :icon="agentIcon"
    />
  </div>
</template>

<script setup lang="ts">
import type { ContextualizedAgentEvent, ChatMessage, ThreadDto } from '@core/sdk/client'

const props = defineProps<{
  messages: ChatMessage[]
  event: ContextualizedAgentEvent
  thread: ThreadDto
  title?: string
}>()

const { t } = useI18n()
const agentIcon = useAgentIconFromThread(props.event, props.thread)

const roleName = (role: string | undefined) => {
  switch (role) {
    case 'user':
      return t('event.contextComposed.user')
    case 'system':
      return t('event.contextComposed.system')
    default:
      return t('event.contextComposed.assistant')
  }
}
</script>
