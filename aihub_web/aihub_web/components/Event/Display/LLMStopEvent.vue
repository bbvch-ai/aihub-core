<template>
  <EventDisplayBase
    :event="props.event"
    title="LLM Stop"
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
    <CostsTable
      :prompt-token-count="event.event.token_count_prompt ?? 0"
      :prompt-tokens-costs="event.event.token_count_prompt / 1000 * event.event.invocation_parameters?.prompt_tokens_costs_per_thousand ?? 0"
      :completion-token-count="event.event.token_count_completion ?? 0"
      :completion-tokens-costs="event.event.token_count_completion / 1000 * event.event.invocation_parameters?.completion_tokens_costs_per_thousand ?? 0"
      :embedding-token-count="0"
      :embedding-tokens-costs="0"
    />
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ChatMessageOutput, LlmStopEvent, WsServerEvent } from '@core/sdk/client'

const props = defineProps<{
  event: WsServerEvent & { event: LlmStopEvent }
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
