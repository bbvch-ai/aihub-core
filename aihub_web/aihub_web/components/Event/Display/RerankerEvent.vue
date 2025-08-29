<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="iconoir:sort"
  >
    <div class="flex flex-col gap-4">
      <IconField class="w-full">
        <InputIcon class="pi pi-search" />
        <InputText
          :model-value="event.event.query"
          class="w-full"
          readonly
        />
      </IconField>
      <p class="pt-5 font-bold">
        Top: {{ event.event.top_k }} relevanteste Dokumente:
      </p>
      <ChatSourceNodes
        :nodes="event.event.output_nodes ?? []"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { RerankerEvent, ThreadDto, AgentEventReadable } from '@core/sdk/client'

defineProps<{
  event: AgentEventReadable & { event: RerankerEvent }
  thread: ThreadDto
}>()
</script>
