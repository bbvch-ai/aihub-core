<template>
  <EventDisplayBase
    is-empty
    :event="event"
    :thread="thread"
    icon="line-md:question"
  />
</template>

<script setup lang="ts">
import type { ThreadDto, WsServerEvent } from '@core/sdk/client'

defineProps<{
  event: WsServerEvent
  thread: ThreadDto
}>()
</script>
