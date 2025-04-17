<template>
  <EventDisplayBase
    :event="event"
    icon="icon-park-twotone:success"
  />
</template>

<script setup lang="ts">
import type { StopEvent, WsServerEvent } from '@core/sdk/client'

defineProps<{
  event: WsServerEvent & { event: StopEvent }
}>()
</script>

<style scoped>

</style>
