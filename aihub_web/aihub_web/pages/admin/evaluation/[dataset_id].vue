<template>
  <StructuralColumn
    title="Dataset"
    close-route="/admin/evaluation"
    :loading="datasetIsLoading"
  >
    <ConfirmPopup />
    <div class="card flex flex-wrap justify-center gap-2">
      <Button
        label="Save"
        outlined
        @click="safeDataset($event)"
      />
    </div>
    <div
      v-for="item in dataset.items"
      :key="item.id"
    >
      <p>Q: {{ item.question }}</p>
      <p>A: {{ item.answer }}</p>
    </div>
    <div class="card grid grid-cols-1 gap-4 md:grid-cols-2">
      <InputGroup>
        <InputGroupAddon>
          <i class="pi pi-user" />
        </InputGroupAddon>
        <InputText
          v-model="question"
          placeholder="Username"
        />
      </InputGroup>
      <InputGroup>
        <InputGroupAddon>
          <i class="pi pi-user" />
        </InputGroupAddon>
        <InputText
          v-model="answer"
          placeholder="Username"
        />
      </InputGroup>
    </div>
    <Button
      type="button"
      label="Add"
      icon="pi pi-search"
      :disabled="!question || !answer"
      @click="add"
    />
  </StructuralColumn>
</template>

<script setup lang="ts">
import { useConfirm } from 'primevue/useconfirm'

import type { DatasetItemCreate } from '@core/sdk/client'

const { dataset, datasetIsLoading } = useDataset()

const addedItems = ref<DatasetItemCreate[]>([])

const question = ref('')
const answer = ref('')
const add = () => {
  addedItems.value.push({
    question: question.value,
    answer: answer.value,
  })
  question.value = ''
  answer.value = ''
}

const confirm = useConfirm()
const toast = useToast()

const { updateDataset } = useUpdateDataset()

const safeDataset = (event) => {
  confirm.require({
    target: event.currentTarget,
    message: 'Are you sure you want to proceed?',
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
      updateDataset({ dataset: { items: addedItems.value } })
      addedItems.value = []
    },
    reject: () => {
      toast.add({ severity: 'error', summary: 'Rejected', detail: 'You have rejected', life: 3000 })
    },
  })
}
</script>

<style scoped>

</style>
