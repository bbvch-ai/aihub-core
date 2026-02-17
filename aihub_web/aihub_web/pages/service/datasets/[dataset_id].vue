<template>
  <StructuralColumn
    :title="dataset?.dataset_name"
    close-route="/service/datasets"
    :loading="datasetIsLoading"
  >
    <ConfirmPopup />
    <div class="flex flex-col gap-3">
      <EvaluationDatasetEdit v-model="editableDataset" />
      <Button
        v-if="changedItems.length > 0"
        class="w-full"
        :label="t('evaluation.dataset.save_button')"
        icon="pi pi-save"
        @click="safeDataset($event)"
      />
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
import cloneDeep from 'lodash.clonedeep'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { useI18n } from 'vue-i18n'

import type { Dataset, DatasetItem, DatasetItemCreate } from '@core/sdk/client'

const { t } = useI18n()

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
    message: t('evaluation.dataset.save_confirmation'),
    icon: 'pi pi-exclamation-triangle',
    rejectProps: {
      label: t('evaluation.dataset.cancel_button'),
      severity: 'secondary',
      outlined: true,
    },
    acceptProps: {
      label: t('evaluation.dataset.save_action'),
    },
    accept: async () => {
      const items = changedItems.value
      if (items.length > 0) {
        await updateDataset({ dataset: { items } })
        toast.add({ severity: 'success', summary: t('evaluation.dataset.saved_summary'), detail: t('evaluation.dataset.saved_detail'), life: 3000 })
      }
    },
  })
}
</script>
