<template>
  <EventDisplayBase
    :event="props.event"
    title="Embedding"
    subtitle="..."
  >
    Embedding Event
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { EmbeddingEvent, WsServerEvent } from '@core/sdk/client'

const props = defineProps<{
  event: WsServerEvent & { event: EmbeddingEvent }
}>()
</script>

<style scoped>

</style>
