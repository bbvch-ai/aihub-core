<template>
  <EventDisplayBase
    :event="event"
    icon="line-md:search-twotone"
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
