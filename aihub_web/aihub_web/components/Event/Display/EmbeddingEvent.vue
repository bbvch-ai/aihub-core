<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="line-md:search-twotone"
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
import type { EmbeddingEvent, ThreadDto, WsServerEventReadable } from '@core/sdk/client'

defineProps<{
  event: WsServerEventReadable & { event: EmbeddingEvent }
  thread: ThreadDto
}>()
</script>
