<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="icon-park-solid:success"
  >
    <div class="flex flex-col gap-3">
      <div class="flex items-center gap-2">
        <Badge
          value="Success"
          severity="success"
        />
        <p class="font-bold">
          {{ event.event.title || event.event.name }}
        </p>
      </div>

      <div
        v-if="event.event.input && Object.keys(event.event.input).length > 0"
        class="grid grid-cols-2 gap-4"
      >
        <InputGroup
          v-for="(val, key) in event.event.input"
          :key="key"
        >
          <Button :label="useChangeCase(key, 'capitalCase')" />
          <InputText
            :placeholder="String(val)"
            readonly
          />
        </InputGroup>
      </div>

      <div
        v-if="event.event.output"
        class="rounded-md bg-surface-50 p-3 dark:bg-surface-800"
      >
        <p class="font-mono text-sm whitespace-pre-wrap break-words">
          {{ event.event.output }}
        </p>
      </div>

      <div
        v-if="event.event.duration"
        class="text-xs text-surface-500"
      >
        Duration: {{ event.event.duration.toFixed(2) }}s
      </div>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import { useChangeCase } from '@vueuse/integrations/useChangeCase'

import type { ToolOutputEventReadable, ThreadDto, AgentEventReadable } from '@core/sdk/client'

defineProps<{
  event: AgentEventReadable & { event: ToolOutputEventReadable }
  thread: ThreadDto
}>()
</script>
