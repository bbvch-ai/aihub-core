<template>
  <EventDisplayBase
    :event="props.event"
    title="Thought"
    subtitle="Internal thought of the agent"
  >
    <p class="border-l-4 border-surface-200 pl-3 italic dark:border-surface-600">
      {{ event.event.content }}
    </p>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ThoughtEvent, WsServerEvent } from '@core/sdk/client'

const props = defineProps<{
  event: WsServerEvent & { event: ThoughtEvent }
}>()
</script>

<style scoped>

</style>
