<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="line-md:document-twotone"
  >
    <div class="flex flex-col gap-4">
      <ChatSourceDocuments
        :documents="event.event.documents ?? []"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { RetrieverEvent, ThreadDto, WsServerEvent } from '@core/sdk/client'

defineProps<{
  event: WsServerEvent & { event: RetrieverEvent }
  thread: ThreadDto
}>()
</script>
