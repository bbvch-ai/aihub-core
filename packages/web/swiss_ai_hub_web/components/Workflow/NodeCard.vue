<template>
  <div
    class="w-[298px] overflow-hidden rounded-xl border bg-surface-50 shadow-md dark:bg-surface-950"
    :class="accent === 'red'
      ? 'border-red-300 dark:border-red-900/60'
      : 'border-surface-200 dark:border-surface-800'"
  >
    <div class="flex flex-row gap-3 p-3">
      <div
        class="mt-1 flex size-12 shrink-0 items-center justify-center rounded-xl"
        :class="accent === 'red'
          ? 'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-300'
          : 'bg-surface-100 dark:bg-surface-800'"
      >
        <Icon
          :name="icon"
          size="1.5em"
        />
      </div>
      <div class="flex flex-col">
        <span class="font-bold">{{ label }}</span>
        <span
          v-if="description"
          class="text-xs text-surface-500"
        >{{ description }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  icon: string
  label: string
  description?: string | null
  accent?: 'neutral' | 'red'
}>(), {
  accent: 'neutral',
  description: null,
})
</script>
