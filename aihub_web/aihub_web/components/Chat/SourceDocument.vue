<template>
  <Card>
    <template
      #header
    >
      <div class="relative flex w-full">
        <div
          class="absolute -right-3 -top-3 rounded px-2 py-1 font-bold"
        >
          <div
            class="flex size-7 items-center justify-center rounded-full text-xs text-white"
            :class="scoreToColor(document.score)"
          >
            {{ scoreToRank(document.score) }}
          </div>
        </div>
      </div>
    </template>
    <template #title>
      {{ document.metadata.document_title ?? "Dokument" }}
    </template>
    <template #content>
      <p class="m-0">
        {{ document.content }}
      </p>
    </template>
    <template #footer>
      <Divider />
      <p
        v-for="(val, key) in document.metadata"
        :key="key"
        class="flex flex-row gap-2"
      >
        <span class="font-bold">{{ useChangeCase(key, 'capitalCase') }}:</span>
        <span>{{ val }}</span>
      </p>
    </template>
  </Card>
</template>

<script setup lang="ts">
import { useChangeCase } from '@vueuse/integrations/useChangeCase'

import type { Document } from '@core/sdk/client'

defineProps<{
  document: Document
}>()

const scoreToColor = (score: number) => {
  if (score <= 0.5) {
    return 'bg-red-700'
  }
  if (score <= 0.75) {
    return 'bg-yellow-700'
  }
  if (score <= 0.85) {
    return 'bg-green-500'
  }
  if (score <= 0.90) {
    return 'bg-green-600'
  }
  if (score <= 0.95) {
    return 'bg-green-700'
  }
  return 'bg-green-800'
}

const scoreToRank = (score: number) => {
  if (score <= 0.5) {
    return 'D'
  }
  if (score <= 0.75) {
    return 'C'
  }
  if (score <= 0.85) {
    return 'B'
  }
  if (score <= 0.90) {
    return 'A'
  }
  if (score <= 0.95) {
    return 'A+'
  }
  return 'A++'
}
</script>

<style scoped>

</style>
