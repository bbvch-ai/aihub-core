<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="vaadin:chat"
  >
    <div class="flex flex-col gap-8">
      <div
        v-for="(message, index) in inputMessages"
        :key="index"
        class="flex flex-col gap-2"
      >
        <ChatMessage
          :message="message"
          :name="message.role == 'user' ? 'User' : event.event.chat_model_name"
          :email="message.role == 'user' ? '' : event.event.provider"
          :date="new Date(event.event.created_at / 1_000_000)"
          :icon="agentIcon"
        />
      </div>
      <hr>
      <div
        v-for="(message, index) in outputMessages"
        :key="index"
        class="flex flex-col gap-2"
      >
        <ChatMessage
          :message="message"
          :name="message.role == 'user' ? 'User' : event.event.chat_model_name"
          :email="message.role == 'user' ? '' : event.event.provider"
          :date="new Date(event.event.created_at / 1_000_000)"
          :icon="agentIcon"
        />
      </div>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type {
  AudioContent,
  ChatMessageOutput,
  ImageContent,
  LlmEventReadable,
  TextContent,
  ThreadDto,
  AgentEventReadable,
} from '@core/sdk/client'

const props = defineProps<{
  event: AgentEventReadable & { event: LlmEventReadable }
  thread: ThreadDto
}>()

const agentIcon = useAgentIconFromThread(props.event, props.thread)

const inputMessages = computed<ChatMessageOutput[]>(() => {
  return props.event.event.input_messages?.map((message) => {
    return {
      role: message.role,
      blocks: message.contents?.map((content: TextContent | ImageContent | AudioContent) => {
        if (content.type === 'text') {
          return {
            block_type: 'text',
            text: content.text,
          }
        }
        if (content.type === 'image') {
          return {
            block_type: 'image',
            path: content.url,
          }
        }
      }),
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
