<template>
  <EventDisplayBase
    :event="props.event"
    title="LLM Interaction"
    subtitle="Marks a completed LLM output"
  >
    <div class="flex flex-col gap-12 py-5">
      <div
        v-for="message in inputMessages"
        class="flex flex-col gap-2"
      >
        <ChatMessage
          :message="message"
          :name="message.role == 'user' ? 'User' : event.event.chat_model_name"
          :preferred-username="message.role == 'user' ? '' : event.event.provider"
        />
      </div>
      <hr>
      <div
        v-for="message in outputMessages"
        class="flex flex-col gap-2"
      >
        <ChatMessage
          :message="message"
          :name="message.role == 'user' ? 'User' : event.event.chat_model_name"
          :preferred-username="message.role == 'user' ? '' : event.event.provider"
        />
      </div>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ChatMessageOutput, LlmEvent, WsServerEvent } from '@core/sdk/client'

const props = defineProps<{
  event: WsServerEvent & { event: LlmEvent }
}>()

const inputMessages = computed<ChatMessageOutput[]>(() => {
  return props.event.event.input_messages?.map((message) => {
    return {
      role: message.role,
      blocks: [
        {
          block_type: 'text',
          text: message.content,
        },
      ],
    }
  }) ?? []
})

const outputMessages = computed<ChatMessageOutput[]>(() => {
  return props.event.event.output_messages?.map((message) => {
    return {
      role: message.role,
      blocks: [
        {
          block_type: 'text',
          text: message.content,
        },
      ],
    }
  }) ?? []
})
</script>
