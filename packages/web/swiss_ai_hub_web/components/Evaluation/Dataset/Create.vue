<template>
  <div>
    <span class="mb-8 block text-surface-500 dark:text-surface-400">
      {{ t('evaluation.dataset.create_description') }}
    </span>
    <div class="mb-4 flex flex-col gap-4">
      <div class="flex flex-col">
        <label
          for="name"
          class="font-semibold"
        >
          {{ t('evaluation.dataset.name') }}
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
          {{ t('evaluation.dataset.description') }}
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
          :label="t('evaluation.dataset.cancel')"
          severity="secondary"
          @click="close"
        />
        <Button
          type="button"
          :label="t('evaluation.dataset.save')"
          :disabled="!dataset.dataset_name || !dataset.description || dataset.items.length === 0"
          @click="save"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { DatasetCreate } from '@core/sdk/client'

const { t } = useI18n()

const dataset = ref<DatasetCreate>({
  dataset_name: '',
  description: '',
  items: [],
})

const { createDataset } = useCreateDataset()
const { tenantId } = useTenant()

const emit = defineEmits<{
  close: []
}>()

const close = () => {
  emit('close')
}
const save = async () => {
  await createDataset({ dataset: dataset.value, tenantId: tenantId.value! })
  emit('close')
}
</script>
