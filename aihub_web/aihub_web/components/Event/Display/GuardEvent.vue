<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="icon-park-twotone:shield"
    is-empty
  />
</template>

<script setup lang="ts">
import type { GuardEvent, ThreadDto, ContextualizedAgentEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: GuardEvent }
  thread: ThreadDto
}>()
</script>
