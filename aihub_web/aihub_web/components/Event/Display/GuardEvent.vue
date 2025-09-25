<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="icon-park-twotone:shield"
    is-empty
  />
</template>

<script setup lang="ts">
import type { GuardEventReadable, ThreadDto, AgentEventReadable } from '@core/sdk/client'

defineProps<{
  event: AgentEventReadable & { event: GuardEventReadable }
  thread: ThreadDto
}>()
</script>
