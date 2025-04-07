<template>
  <EventDisplayBase
    :event="event"
    title="Dokumente sortieren"
    icon="iconoir:sort"
    subtitle="Sortiere Dokumente nach Relevanz und wähle die passendsten Dokumente für die Aufgabe aus."
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
      <ChatSourceDocument
        v-for="document in event.event.output_documents"
        :key="document.id"
        :document="document"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { RerankerEvent, WsServerEvent } from '@core/sdk/client'

defineProps<{
  event: WsServerEvent & { event: RerankerEvent }
}>()
</script>

<style scoped>

</style>
