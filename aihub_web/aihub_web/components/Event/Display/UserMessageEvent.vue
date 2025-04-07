<template>
  <EventDisplayBase
    :event="event"
    icon="line-md:chat-filled"
    title="Anfrage via Chat"
    subtitle="Der Assistent hat eine Nachricht vom Benutzer erhalten, die er zu beantworten versucht. Falls bereits ein Chatverlauf existiert wird dieser dem Assistenten ebenfalls zur Verfügung gestellt"
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
import type { UserMessageEvent, WsServerEvent } from '@core/sdk/client'

defineProps<{
  event: WsServerEvent & { event: UserMessageEvent }
}>()
</script>
