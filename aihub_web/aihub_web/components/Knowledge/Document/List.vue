<template>
  <DataTable
    :value="documents"
    table-style="min-width: 50rem"
    selection-mode="single"
    :selection="selectedDocument"
    :row-class="getRowClass"
    @update:selection="handleSelection"
  >
    <Column
      field="title"
      :header="t('document.list.title')"
    >
      <template #body="{ data }">
        <div class="flex items-center gap-2">
          <p
            class="font-bold"
          >
            {{ data.document_title }}
          </p>
          <div
            v-if="!data.is_ingested"
            class="flex items-center gap-2"
          >
            <Tag
              :value="t('document.list.is_processing')"
              size="small"
              icon="pi pi-clock"
              severity="info"
            />
          </div>
        </div>
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
      field="number_of_pages"
      :header="t('document.list.number_of_pages')"
    >
      <template #body="{ data }">
        <Badge
          :value="data.number_of_pages ?? '-'"
        />
      </template>
    </Column>
    <Column
      field="source"
      :header="t('document.list.download')"
    >
      <template #body="{ data }">
        <Button
          v-if="data.source_path"
          rounded
          size="small"
          variant="outlined"
          icon="pi pi-download"
          @click="() => downloadFile(data.source_path)"
        />
        <span
          v-else
          class="text-sm text-surface-400"
        >-</span>
      </template>
    </Column>
  </DataTable>
</template>

<script setup lang="ts">
import type { DocumentDto } from '@core/sdk/client'

const route = useRoute()
const { t } = useI18n()
const { getDocumentSourceUrl } = useDocumentUrl()

const props = defineProps<{
  documents: DocumentDto[]
}>()

const emit = defineEmits<{
  selected: [document: DocumentDto]
}>()

const formatted = (datestr: string) => useDateFormat(new Date(datestr), 'DD.MM.YYYY')
const selectedDocument = computed(() => {
  return props.documents.filter((document: DocumentDto) => {
    return document.id === route.params.document_id
  })
})

const handleSelection = (document: DocumentDto) => {
  if (document.is_ingested) {
    emit('selected', document)
  }
}

const getRowClass = (data: DocumentDto) => {
  return data.is_ingested ? '' : 'opacity-50 cursor-not-allowed pointer-events-none'
}

const downloadFile = async (src: string) => {
  const url = await getDocumentSourceUrl(src)
  window.open(url, '_blank')
}
</script>
