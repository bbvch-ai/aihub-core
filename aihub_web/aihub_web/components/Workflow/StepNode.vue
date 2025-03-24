<template>
  <div class="bg-stone-50 dark:bg-stone-950 rounded-md shadow-md border border-stone-100 dark:border-stone-800 overflow-hidden w-[500px]">
    <div class="h-1 w-full bg-red-500" />
    <div class="flex flex-row gap-3 p-3">
      <div class="rounded-full bg-stone-200 dark:bg-stone-600 w-8 h-8 flex items-center justify-center mt-1">
        <Icon
          :name="props.data.icon ?? 'mingcute:ai-fill'"
          size="0.8em"
        />
      </div>
      <div class="flex flex-col">
        <span class="font-bold">{{ props.data.label }}</span>
        <span class="text-xs">{{ props.data.description }}</span>
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
    <div class="w-full flex flex-row gap-2 p-3">
      <div class="w-1/2 flex flex-col gap-2">
        <div
          v-for="(event_specs, event_name) in props.data.input_events"
          :key="event_name"
          class="flex flex-col gap-2"
        >
          <EventSpecs
            :events="event_specs.event_types"
            type="input"
          />
        </div>
      </div>
      <div class="w-1/2 flex flex-col gap-2">
        <EventSpecs
          v-if="props.data.output_events"
          :events="props.data.output_events"
          type="output"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import type { NodeData } from '@core/sdk/client'
import EventSpecs from '@core/components/Workflow/EventSpecs.vue'

const props = defineProps<{
  id: string
  data: NodeData
}>()
</script>
