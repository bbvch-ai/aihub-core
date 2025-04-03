<template>
  <EventDisplayBase
    :event="event"
    title="Stop"
    subtitle="Der Assistent hat seine Aufgabe erledigt und gibt das Wort zurück an den Benutzer"
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
