<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:question-mark-circle"
  >
    <div class="flex flex-col gap-2">
      <span class="text-sm font-medium text-surface-600 dark:text-surface-400">
        <Icon
          name="mage:archive"
          class="size-4"
        />
        {{ t('event.standaloneQuestionCondenser.condensedQuestion') }}
      </span>
      <ChatMessage
        :message="event.event.condensed_chat_message"
        :name="t('event.standaloneQuestionCondenser.user')"
        :icon="agentIcon"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type {
  StandaloneQuestionCondenserEvent,
  ThreadDto,
  ContextualizedAgentEvent,
} from '@core/sdk/client'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: StandaloneQuestionCondenserEvent }
  thread: ThreadDto
}>()

const { t } = useI18n()
const agentIcon = useAgentIconFromThread(props.event, props.thread)
</script>
