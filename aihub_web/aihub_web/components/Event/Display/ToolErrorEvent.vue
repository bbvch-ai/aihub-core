<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="icon-park-solid:close-one"
  >
    <div class="flex flex-col gap-3">
      <div class="flex items-center gap-2">
        <Badge
          value="Error"
          severity="danger"
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

      <div class="rounded-md bg-red-50 p-3 dark:bg-red-900/20">
        <p class="font-mono text-sm text-red-700 whitespace-pre-wrap break-words dark:text-red-400">
          {{ event.event.error }}
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

import type { ToolErrorEventReadable, ThreadDto, AgentEventReadable } from '@core/sdk/client'

defineProps<{
  event: AgentEventReadable & { event: ToolErrorEventReadable }
  thread: ThreadDto
}>()
</script>
