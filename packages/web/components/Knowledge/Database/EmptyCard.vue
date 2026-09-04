<template>
  <button
    type="button"
    class="flex w-full cursor-pointer items-center gap-3 rounded-xl border-2 border-dashed border-surface-300 p-4 text-left hover:border-primary-500 hover:bg-surface-50 dark:border-surface-600 dark:hover:bg-surface-800"
    @click="handleAdd"
  >
    <div class="flex items-center justify-center p-2">
      <i
        class="pi pi-database text-surface-400"
        style="font-size: 1.5rem"
      />
    </div>
    <div>
      <h3 class="font-medium text-surface-600 dark:text-surface-400">
        {{ t('knowledge.add_database.title') }}
      </h3>
      <p class="text-sm text-surface-500 dark:text-surface-400">
        {{ t('knowledge.add_database.description') }}
      </p>
    </div>
  </button>
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
