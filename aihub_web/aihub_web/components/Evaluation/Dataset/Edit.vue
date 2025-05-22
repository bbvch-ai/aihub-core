<template>
  <div class="flex flex-col gap-4">
    <p
      v-if="modelValue.items.length === 0"
      class="text-sm text-surface-500 dark:text-surface-400"
    >
      Add at least 1 Datapoint
    </p>
    <DataTable
      v-else
      :value="modelValue.items"
    >
      <Column
        field="question"
        header="Question"
      />
      <Column
        field="answer"
        header="Answer"
      />
      <Column
        header="Status"
        class="w-24 !text-end"
      >
        <template #body="{ data: item }">
          <Tag
            v-if="isTemporaryItem(item)"
            value="New"
            severity="success"
          />
        </template>
      </Column>
      <Column class="w-12">
        <template #body="{ data: item }">
          <Button
            v-if="isTemporaryItem(item)"
            icon="pi pi-times"
            severity="secondary"
            variant="text"
            rounded
            size="small"
            @click="removeItem(item)"
          />
        </template>
      </Column>
    </DataTable>
    <div class="flex gap-2">
      <InputGroup>
        <InputGroupAddon>
          <i class="pi pi-question" />
        </InputGroupAddon>
        <InputText
          v-model="question"
          placeholder="Question"
          @click.enter="add"
        />
      </InputGroup>
      <InputGroup>
        <InputGroupAddon>
          <i class="pi pi-check" />
        </InputGroupAddon>
        <InputText
          v-model="answer"
          placeholder="Answer"
          @click.enter="add"
        />
      </InputGroup>
      <div>
        <Button
          type="button"
          label="Add"
          icon="pi pi-search"
          :disabled="!question || !answer"
          @click="add"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Dataset, DatasetCreate, DatasetItem } from '@core/sdk/client'

const props = defineProps<{
  modelValue: Dataset | DatasetCreate
}>()

const emit = defineEmits<{
  'update:modelValue': [Dataset]
}>()

const { cloned: dataset } = useCloned<Dataset>(
  () => props.modelValue,
  { deep: true },
)

const question = ref('')
const answer = ref('')
const add = () => {
  if (!question.value || !answer.value) {
    return
  }
  if (!dataset.value.items) {
    dataset.value.items = []
  }
  dataset.value.items.push({
    question: question.value,
    answer: answer.value,
    id: `tmp-${new Date().getTime()}`,
  })
  question.value = ''
  answer.value = ''
  emit('update:modelValue', dataset.value)
}

const removeItem = (itemToRemove: DatasetItem) => {
  if (!dataset.value.items) return
  dataset.value.items = dataset.value.items.filter(
    (datasetItem: DatasetItem) => datasetItem.id !== itemToRemove.id,
  )
  emit('update:modelValue', dataset.value)
}

const isTemporaryItem = (item: DatasetItem) => {
  return !item.id || item.id.startsWith('tmp')
}
</script>

<style scoped>

</style>
