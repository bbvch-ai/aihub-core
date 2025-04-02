<template>
  <EventDisplayBase :event="props.event">
    Unknown: {{ props.event }}
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type {WsServerEvent} from "@core/sdk/client";

const props = defineProps<{
  event: WsServerEvent
}>()
</script>

