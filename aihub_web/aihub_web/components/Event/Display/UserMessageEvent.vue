<template>
  <EventDisplayBase
    :event="props.event"
    title="User Message"
    subtitle="Message sent to a user to an Agent"
  >
    <div class="flex flex-col gap-12 py-5">
      <div
        v-for="message in props.event.event.messages"
        class="flex flex-col gap-2"
      >
        <ChatMessage
          :message="message"
          :name="message.role == 'user' ? props.event.event.user.name : message.role"
          :preferred-username="message.role == 'user' ? props.event.event.user.preferred_username : ''"
        />
      </div>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { UserMessageEvent, WsServerEvent } from '@core/sdk/client'

const props = defineProps<{
  event: WsServerEvent & { event: UserMessageEvent }
}>()
</script>
