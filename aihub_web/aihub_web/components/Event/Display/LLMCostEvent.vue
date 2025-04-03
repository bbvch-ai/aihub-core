<template>
  <EventDisplayBase
    :event="event"
    title="Kosten"
    subtitle="Bei der Interaktion mit dem Sprachmodell sind Kosten entstanden, die hier aufgelistet sind."
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
import type { LlmCostEvent, WsServerEvent } from '@core/sdk/client'

defineProps<{
  event: WsServerEvent & { event: LlmCostEvent }
}>()
</script>
