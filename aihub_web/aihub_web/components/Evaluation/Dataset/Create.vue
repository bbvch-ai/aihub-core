<template>
  <div>
    <span class="mb-8 block text-surface-500 dark:text-surface-400">Dataset Information.</span>
    <div class="mb-4 flex items-center gap-4">
      <label
        for="name"
        class="w-24 font-semibold"
      >Name</label>
      <InputText
        id="name"
        v-model="dataset.dataset_name"
        class="flex-auto"
        autocomplete="off"
      />
      <label
        for="description"
        class="w-24 font-semibold"
      >Name</label>
      <InputText
        id="description"
        v-model="dataset.description"
        class="flex-auto"
        autocomplete="off"
      />
      <div class="flex justify-end gap-2">
        <Button
          type="button"
          label="Cancel"
          severity="secondary"
          @click="close"
        />
        <Button
          type="button"
          label="Save"
          @click="save"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DatasetCreate } from '@core/sdk/client'

const dataset = reactive<DatasetCreate>({
  dataset_name: '',
  description: '',
  items: [{
    question: 'This is a question',
    answer: 'This is an answer',
  }],
})

const { createDataset } = useCreateDataset()

const emit = defineEmits<{
  close: []
}>()

const close = () => {
  emit('close')
}
const save = () => {
  createDataset({ dataset })
}
</script>

<style scoped>

</style>
