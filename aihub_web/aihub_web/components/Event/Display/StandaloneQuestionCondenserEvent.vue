<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="material-symbols:quiz"
  >
    <div class="flex flex-col gap-8">
      <div class="flex items-center gap-2 text-sm font-medium text-surface-600 dark:text-surface-400">
        <Icon
          name="material-symbols:compress"
          class="size-4"
        />
        <span>{{ t('event.standaloneQuestionCondenser.summary') }}</span>
      </div>

      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label class="text-sm font-medium text-surface-600 dark:text-surface-400">
            {{ t('event.standaloneQuestionCondenser.condensedQuestion') }}
          </label>
          <div class="rounded-lg bg-surface-50 p-4 dark:bg-surface-800">
            <ChatMessage
              :message="event.event.condensed_chat_message"
              :name="t('event.standaloneQuestionCondenser.user')"
              :preferred-username="''"
              :date="new Date(event.event.created_at / 1_000_000)"
              :icon="agentIcon"
            />
          </div>
        </div>
      </div>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type {
  StandaloneQuestionCondenserEventReadable,
  ThreadDto,
  AgentEventReadable,
} from '@core/sdk/client'

const props = defineProps<{
  event: AgentEventReadable & { event: StandaloneQuestionCondenserEventReadable }
  thread: ThreadDto
}>()

const { t } = useI18n()
const agentIcon = useAgentIconFromThread(props.event, props.thread)
</script>
