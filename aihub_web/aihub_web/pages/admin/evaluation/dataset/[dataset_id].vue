<template>
  <StructuralColumn
    title="Dataset"
    close-route="/admin/evaluation"
    :loading="datasetIsLoading"
  >
    <ConfirmPopup />
    <div class="flex flex-col gap-3">
      <EvaluationDatasetEdit v-model="editableDataset" />
      <Button
        v-if="changedItems.length > 0"
        class="w-full"
        label="Save Dataset"
        icon="pi pi-save"
        @click="safeDataset($event)"
      />
    </div>
    <Toast />
  </StructuralColumn>
</template>

<script setup lang="ts">
import cloneDeep from 'lodash.clonedeep'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'

import type { Dataset, DatasetItem, DatasetItemCreate } from '@core/sdk/client'

const { dataset, datasetIsLoading } = useDataset()
const editableDataset = ref<Dataset | null>(null)

watch(dataset, (newServerData) => {
  if (newServerData) {
    editableDataset.value = cloneDeep(newServerData)
  }
}, { immediate: true })

const confirm = useConfirm()
const toast = useToast()

const { updateDataset } = useUpdateDataset()

const changedItems = computed<DatasetItemCreate[]>(() => {
  return editableDataset.value.items
    .filter((item: DatasetItem) => {
      return !item.id || item.id.startsWith('tmp')
    })
    .map((item: DatasetItem) => {
      return {
        question: item.question,
        answer: item.answer,
      }
    })
})

const safeDataset = (event) => {
  confirm.require({
    target: event.currentTarget,
    message: 'Save dataset? Once added, you can not remove items again.',
    icon: 'pi pi-exclamation-triangle',
    rejectProps: {
      label: 'Cancel',
      severity: 'secondary',
      outlined: true,
    },
    acceptProps: {
      label: 'Save',
    },
    accept: () => {
      const items = changedItems.value
      if (items.length > 0) {
        updateDataset({ dataset: { items } })
        toast.add({ severity: 'success', summary: 'Saved', detail: 'Dataset saved', life: 3000 })
      }
    },
  })
}
</script>

<style scoped>

</style>
