<template>
  <EventDisplayBase
    :event="event"
    title="Suche nach Information"
    icon="line-md:search-twotone"
    subtitle="Der Agent sucht in seinem Wissensspeicher nach Informationen, die er für die Beantwortung der Anfrage benötigt."
  >
    <IconField class="w-full">
      <InputIcon class="pi pi-search" />
      <InputText
        :model-value="event.event.text"
        class="w-full"
        readonly
      />
    </IconField>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { EmbeddingEvent, WsServerEvent } from '@core/sdk/client'

defineProps<{
  event: WsServerEvent & { event: EmbeddingEvent }
}>()
</script>

<style scoped>

</style>
