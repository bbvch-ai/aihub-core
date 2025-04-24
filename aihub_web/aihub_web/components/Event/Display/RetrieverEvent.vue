<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="line-md:document-twotone"
  >
    <div class="flex flex-col gap-4">
      <ChatSourceDocument
        v-for="document in event.event.documents"
        :key="document.id"
        :document="document"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { RetrieverEvent, ThreadResponse, WsServerEvent } from '@core/sdk/client'

defineProps<{
  event: WsServerEvent & { event: RetrieverEvent }
  thread: ThreadResponse
}>()
</script>

<style scoped>

</style>
