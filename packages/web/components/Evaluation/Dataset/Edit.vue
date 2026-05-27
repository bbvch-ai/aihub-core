<template>
  <div class="flex flex-col gap-4">
    <p
      v-if="modelValue.items.length === 0"
      class="text-sm text-surface-500 dark:text-surface-400"
    >
      {{ t('evaluation.dataset.add_at_least_one') }}
    </p>
    <DataTable
      v-else
      :value="modelValue.items"
      size="small"
    >
      <Column
        field="question"
        :header="t('evaluation.dataset.question_header')"
      />
      <Column
        field="answer"
        :header="t('evaluation.dataset.answer_header')"
      />
      <Column
        :header="t('evaluation.dataset.status')"
        class="w-24 !text-end"
      >
        <template #body="{ data: item }">
          <Tag
            v-if="isTemporaryItem(item)"
            :value="t('evaluation.dataset.new')"
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
          :placeholder="t('evaluation.dataset.question_placeholder')"
          @click.enter="add"
        />
      </InputGroup>
      <InputGroup>
        <InputGroupAddon>
          <i class="pi pi-check" />
        </InputGroupAddon>
        <InputText
          v-model="answer"
          :placeholder="t('evaluation.dataset.answer_placeholder')"
          @click.enter="add"
        />
      </InputGroup>
      <div>
        <Button
          type="button"
          :label="t('evaluation.dataset.add_button')"
          icon="pi pi-plus"
          :disabled="!question || !answer"
          @click="add"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { Dataset, DatasetCreate, DatasetItem } from '@core/sdk/client'

const { t } = useI18n()

const props = defineProps<{
  modelValue: Dataset | DatasetCreate
}>()

const emit = defineEmits<{
  'update:modelValue': [Dataset]
}>()

const dataset = ref<Dataset | DatasetCreate>(props.modelValue)
watch(() => props.modelValue, (newValue: Dataset | DatasetCreate) => {
  dataset.value = newValue
}, { deep: true })

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
