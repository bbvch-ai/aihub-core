<template>
  <DataTable
    :value="documents"
    table-style="min-width: 50rem"
    selection-mode="single"
    @update:selection="emit('selected', $event)"
  >
    <Column
      field="title"
      :header="t('document.list.title')"
    >
      <template #body="{ data }">
        <p class="font-bold">
          {{ data.title }}
        </p>
      </template>
    </Column>
    <Column
      field="Created"
      :header="t('document.list.created')"
    >
      <template #body="{ data }">
        <p>{{ formatted(data.created_at) }}</p>
      </template>
    </Column>
    <Column
      field="Updated"
      :header="t('document.list.updated_at')"
    >
      <template #body="{ data }">
        <p>{{ formatted(data.updated_at) }}</p>
      </template>
    </Column>
    <Column
      field="document_type"
      :header="t('document.list.document_type')"
    >
      <template #body="{ data }">
        <Tag
          severity="secondary"
          :value="data.content_type"
        />
      </template>
    </Column>
    <Column
      field="number_of_pages"
      :header="t('document.list.number_of_pages')"
    >
      <template #body="{ data }">
        <Badge
          :value="data.number_of_pages"
          size="large"
        />
      </template>
    </Column>
  </DataTable>
</template>

<script setup lang="ts">
import type { DocumentDto } from '@core/sdk/client'

const { t } = useI18n()

defineProps<{
  documents: DocumentDto[]
}>()

const emit = defineEmits<{
  selected: [document: DocumentDto]
}>()

const formatted = (datestr: string) => useDateFormat(new Date(datestr), 'DD.MM.YYYY')
</script>
