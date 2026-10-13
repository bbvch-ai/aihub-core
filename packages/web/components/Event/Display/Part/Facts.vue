<template>
  <dl class="grid grid-cols-[max-content_1fr] gap-x-6 gap-y-2 text-sm">
    <template
      v-for="fact in shownFacts"
      :key="fact.label"
    >
      <dt class="text-surface-500 dark:text-surface-400">
        {{ fact.label }}
      </dt>
      <dd class="break-words text-surface-800 dark:text-surface-200">
        <div
          v-if="Array.isArray(fact.value)"
          class="flex flex-wrap gap-1"
        >
          <Tag
            v-for="item in fact.value"
            :key="item"
            :value="item"
            severity="secondary"
          />
          <span v-if="fact.value.length === 0">–</span>
        </div>
        <span v-else>{{ fact.value }}</span>
      </dd>
    </template>
  </dl>
</template>

<script setup lang="ts">
import type { EventFact } from '@core/types/EventFact'

const props = defineProps<{
  facts: EventFact[]
}>()

const shownFacts = computed<EventFact[]>(() =>
  props.facts.filter(fact => fact.value !== null && fact.value !== undefined && fact.value !== ''),
)
</script>
