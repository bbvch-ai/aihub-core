<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:search"
  >
    <IconField class="w-full">
      <InputIcon class="pi pi-search" />
      <InputText
        :model-value="event.event.text"
        class="w-full"
        readonly
      />
    </IconField>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { EmbeddingEvent, ThreadDto, ContextualizedAgentEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: EmbeddingEvent }
  thread: ThreadDto
}>()
</script>
