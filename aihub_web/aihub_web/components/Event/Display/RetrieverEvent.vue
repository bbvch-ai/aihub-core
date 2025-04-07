<template>
  <EventDisplayBase
    :event="event"
    title="Dokumente Gefunden"
    icon="line-md:document-twotone"
    subtitle="Der Assistent hat Dokumente gefunde, welche ihm bei seiner Aufgabe hilfreich sein könnten"
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
import type { RetrieverEvent, WsServerEvent } from '@core/sdk/client'

defineProps<{
  event: WsServerEvent & { event: RetrieverEvent }
}>()
</script>

<style scoped>

</style>
