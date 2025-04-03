<template>
  <EventDisplayBase
    :event="event"
    title="Tool"
    subtitle="Internal thought of the agent"
  >
    <p class="text-2xl font-bold">
      {{ event.event.name }}
    </p>
    <p class="font-bold">
      {{ event.event.description }}
    </p>
    <br>
    <div class="grid grid-cols-2 gap-4">
      <InputGroup
        v-for="(val, key) in event.event.parameters"
        :key="key"
      >
        <Button :label="useChangeCase(key, 'capitalCase')" />
        <InputText
          :placeholder="val"
          readonly
        />
      </InputGroup>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import { useChangeCase } from '@vueuse/integrations/useChangeCase'

import type { ToolEvent, WsServerEvent } from '@core/sdk/client'

defineProps<{
  event: WsServerEvent & { event: ToolEvent }
}>()
</script>

<style scoped>

</style>
