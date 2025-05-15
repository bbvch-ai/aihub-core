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
    />
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
</script>
