<template>
  <div class="w-[500px] overflow-hidden rounded-xl border border-surface-200 bg-surface-50 shadow-md dark:border-surface-800 dark:bg-surface-950">
    <div class="flex flex-row gap-3 p-3">
      <div class="mt-1 flex size-8 items-center justify-center rounded-xl bg-surface-200 dark:bg-surface-600">
        <Icon
          :name="data.icon ?? 'mingcute:ai-fill'"
          size="0.8em"
        />
      </div>
      <div class="flex flex-col">
        <span class="font-bold">{{ data.label }}</span>
        <span class="text-xs">{{ data.description }}</span>
      </div>

      <Handle
        type="target"
        :position="Position.Left"
      />
      <Handle
        type="source"
        :position="Position.Right"
        :connectable="false"
      />
    </div>
    <div class="flex w-full flex-row gap-2 p-3">
      <div class="flex w-1/2 flex-col gap-2">
        <div
          v-for="(event_specs, event_name) in data.input_events"
          :key="event_name"
          class="flex flex-col gap-2"
        >
          <EventSpecs
            :events="event_specs.event_names"
            type="input"
          />
        </div>
      </div>
      <div class="flex w-1/2 flex-col gap-2">
        <EventSpecs
          v-if="data.output_events"
          :events="data.output_events"
          type="output"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import EventSpecs from '@core/components/Workflow/EventSpecs.vue'
import { Handle, Position } from '@vue-flow/core'

import type { NodeData } from '@core/sdk/client'

defineProps<{
  id: string
  data: NodeData
}>()
</script>
