<template>
  <div>
    <span class="mb-8 block text-surface-500 dark:text-surface-400">
      Create a new dataset that you can use to evaluate the performance of your Assitants!
    </span>
    <div class="mb-4 flex flex-col gap-4">
      <div class="flex flex-col">
        <label
          for="name"
          class="font-semibold"
        >
          Name
        </label>
        <InputText
          id="name"
          v-model="dataset.dataset_name"
          class="flex-auto"
          autocomplete="off"
        />
      </div>
      <div class="flex flex-col">
        <label
          for="description"
          class="w-24 font-semibold"
        >
          Description
        </label>
        <Textarea
          id="description"
          v-model="dataset.description"
          class="flex-auto"
          autocomplete="off"
        />
      </div>
      <EvaluationDatasetEdit v-model="dataset" />
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
          :disabled="!dataset.dataset_name || !dataset.description || dataset.items.length === 0"
          @click="save"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DatasetCreate } from '@core/sdk/client'

const dataset = ref<DatasetCreate>({
  dataset_name: '',
  description: '',
  items: [],
})

const { createDataset } = useCreateDataset()

const emit = defineEmits<{
  close: []
}>()

const close = () => {
  emit('close')
}
const save = () => {
  createDataset({ dataset: dataset.value })
  emit('close')
}
</script>
