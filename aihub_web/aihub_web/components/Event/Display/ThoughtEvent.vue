<template>
  <EventDisplayBase
    :event="event"
    title="Interner Gedanke"
    icon="mingcute:thought-fill"
    subtitle="Der Agent teilt einen Gedankenschritt mit, welcher ihm dabei hilft, näher zur Erfüllung seiner Aufgabe zu kommen."
  >
    <p class="border-l-4 border-surface-200 pl-3 italic dark:border-surface-600">
      {{ event.event.reasoning_content }}
    </p>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ThoughtEvent, WsServerEvent } from '@core/sdk/client'

defineProps<{
  event: WsServerEvent & { event: ThoughtEvent }
}>()
</script>

<style scoped>

</style>
