<template>
  <EventDisplayBase
    :event="props.event"
    title="Reranking"
    subtitle="..."
  >
    RerankerEvent
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { RerankerEvent, WsServerEvent } from '@core/sdk/client'

const props = defineProps<{
  event: WsServerEvent & { event: RerankerEvent }
}>()
</script>

<style scoped>

</style>
