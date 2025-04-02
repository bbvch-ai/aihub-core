<template>
  <EventDisplayBase
    :event="props.event"
    title="Retrieval"
    subtitle="..."
  >
    Embedding Event
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { RetrieverEvent, WsServerEvent } from '@core/sdk/client'

const props = defineProps<{
  event: WsServerEvent & { event: RetrieverEvent }
}>()
</script>

<style scoped>

</style>
