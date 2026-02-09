<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:message"
    is-external
  >
    <div class="flex flex-col gap-8">
      <div
        v-for="(message, index) in event.event.messages"
        :key="index"
        class="flex flex-col gap-2"
      >
        <ChatMessage
          :message="message"
          :name="message.role == 'user' ? event.event.user.name : message.role"
          :email="message.role == 'user' ? event.event.user.email : ''"
          :date="new Date(event.event.created_at / 1_000_000)"
          :icon="agentIcon"
        />
      </div>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ThreadDto, UserMessageEvent, ContextualizedAgentEvent } from '@core/sdk/client'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: UserMessageEvent }
  thread: ThreadDto
}>()

const agentIcon = useAgentIconFromThread(props.event, props.thread)
</script>
