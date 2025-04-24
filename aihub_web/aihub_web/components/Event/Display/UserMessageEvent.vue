<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="line-md:chat-filled"
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
          :preferred-username="message.role == 'user' ? event.event.user.preferred_username : ''"
        />
      </div>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ThreadResponse, UserMessageEvent, WsServerEvent } from '@core/sdk/client'

defineProps<{
  event: WsServerEvent & { event: UserMessageEvent }
  thread: ThreadResponse
}>()
</script>
