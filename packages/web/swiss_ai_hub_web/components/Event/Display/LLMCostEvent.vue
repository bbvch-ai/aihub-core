<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:dollar"
  >
    <CostsTable
      :prompt-token-count="event.event.prompt_token_count"
      :prompt-tokens-costs="event.event.prompt_tokens_costs"
      :completion-token-count="event.event.completion_token_count"
      :completion-tokens-costs="event.event.completion_tokens_costs"
      :embedding-token-count="event.event.embedding_token_count"
      :embedding-tokens-costs="event.event.embedding_tokens_costs"
    />
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { LlmCostEvent, ThreadDto, ContextualizedAgentEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: LlmCostEvent }
  thread: ThreadDto
}>()
</script>
