<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mynaui:tool"
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

import type { ThreadDto, ToolEvent, ContextualizedAgentEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: ToolEvent }
  thread: ThreadDto
}>()
</script>
