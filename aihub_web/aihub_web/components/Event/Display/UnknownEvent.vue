<template>
  <EventDisplayBase :event="event">
    Unknown: {{ event }}
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { WsServerEvent } from '@core/sdk/client'

defineProps<{
  event: WsServerEvent
}>()
</script>
