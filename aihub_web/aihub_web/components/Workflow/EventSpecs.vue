<template>
  <Accordion
    v-for="event in events"
    :key="event.name"
    value="0"
  >
    <AccordionPanel
      class="bg-white dark:bg-stone-900 p-1 pl-2 rounded-md border-stone-300 dark:border-stone-600"
      :class="{ 'border-l-2': props.type == 'input', 'border-r-2': props.type == 'output' }"
      :value="event.name"
    >
      <AccordionHeader class="text-xs p-1 pl-0 pb-0 text-stone-900 dark:text-stone-100 font-normal">
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
              <span class="text-[9px] italic text-stone-400">{{ payload_value.type }}</span>
            </div>
            <span class="text-[9px] border-stone-200  border-l-2 pl-2">{{ payload_value.description }}</span>
          </div>
        </div>
      </AccordionContent>
    </AccordionPanel>
  </Accordion>
</template>

<script setup lang="ts">
const props = defineProps<{
  events: {
    name: string
    payload: { [key: string]: { type: string, description: string } }
  }[]
  type: string
}>()
</script>
