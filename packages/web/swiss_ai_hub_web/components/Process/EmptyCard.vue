<template>
  <div
    class="flex cursor-pointer flex-col justify-center gap-3 rounded-xl border-2 border-dashed border-surface-300 p-4 hover:border-primary-500 hover:bg-surface-50 dark:border-surface-600 dark:hover:bg-surface-800"
    @click="handleAdd"
  >
    <div class="flex items-center justify-center">
      <div class="flex items-center justify-center p-3">
        <i
          class="pi pi-plus-circle text-surface-400"
          style="font-size: 1.5rem"
        />
      </div>
    </div>
    <div class="text-center">
      <h3 class="font-medium text-surface-600 dark:text-surface-400">
        {{ t('process.add_instance.title') }}
      </h3>
      <p class="text-sm text-surface-500 dark:text-surface-400">
        {{ t('process.add_instance.description') }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n()

const emit = defineEmits<{
  add: []
}>()

const handleAdd = () => {
  emit('add')
}
</script>
