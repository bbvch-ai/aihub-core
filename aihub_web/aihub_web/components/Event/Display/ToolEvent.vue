<template>
  <EventDisplayBase
    :event="props.event"
    title="Tool"
    subtitle="Internal thought of the agent"
  >
    Tool
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ToolEvent, WsServerEvent } from '@core/sdk/client'

const props = defineProps<{
  event: WsServerEvent & { event: ToolEvent }
}>()
</script>

<style scoped>

</style>
