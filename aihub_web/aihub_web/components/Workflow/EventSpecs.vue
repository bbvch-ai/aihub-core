<template>
  <Accordion
    v-for="event in events"
    :key="event.name"
    value="0"
  >
    <AccordionPanel
      class="rounded-md border-surface-300 bg-white p-1 pl-2 dark:border-surface-600 dark:bg-surface-900"
      :class="{ 'border-l-2': type == 'input', 'border-r-2': type == 'output' }"
      :value="event.name"
    >
      <AccordionHeader class="p-1 pb-0 pl-0 text-xs font-normal text-surface-900 dark:text-surface-100">
        {{ event.name }}
      </AccordionHeader>
      <AccordionContent
        class="!p-0 text-xs"
        :pt="{ content: { class: 'p-1 pl-0' } }"
      >
        <div class="flex flex-col gap-2">
          <div
            v-for="(payload_value, payload_name) in event.payload"
            :key="payload_name"
            class="flex flex-col"
          >
            <div class="flex flex-row gap-1">
              <span class="text-[9px] font-bold">{{ payload_name }}</span>
              <span class="text-[9px] italic text-surface-400">{{ payload_value.type }}</span>
            </div>
            <span class="border-l-2 border-surface-200 pl-2 text-[9px] dark:border-surface-700">{{ payload_value.description }}</span>
          </div>
        </div>
      </AccordionContent>
    </AccordionPanel>
  </Accordion>
</template>

<script setup lang="ts">
import type { EventInfo } from '@core/sdk/client'

defineProps<{
  events: EventInfo[]
  type: string
}>()
</script>
