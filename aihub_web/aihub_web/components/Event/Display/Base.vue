<template>
  <Card class="!rounded-2xl bg-surface-50 dark:!bg-surface-800">
    <!--    <template #header> -->
    <!--      <div class="flex justify-end p-3"> -->
    <!--        <Tag -->
    <!--          class="text-xs font-normal text-stone-400" -->
    <!--          severity="secondary" -->
    <!--        > -->
    <!--          Thread: {{ props.event.thread_id }} -->
    <!--        </Tag> -->
    <!--        <Tag -->
    <!--          class="text-xs font-normal text-stone-400" -->
    <!--          severity="secondary" -->
    <!--        > -->
    <!--          Display: {{ props.event.display_id }} -->
    <!--        </Tag> -->
    <!--        <Tag -->
    <!--          class="text-xs font-normal text-stone-400" -->
    <!--          severity="secondary" -->
    <!--        > -->
    <!--          Run: {{ props.event.run_id }} -->
    <!--        </Tag> -->
    <!--      </div> -->
    <!--    </template> -->
    <template #title>
      <span class="font-bold">{{ title }}</span>
    </template>
    <template #subtitle>
      {{ subtitle }}
    </template>
    <template #content>
      <slot />
    </template>
  </Card>
</template>

<script setup lang="ts">
import type { WsServerEvent } from '@core/sdk/client'

const props = defineProps<{
  event: WsServerEvent
  title: string
  subtitle: string
}>()
</script>
