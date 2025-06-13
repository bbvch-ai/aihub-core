<template>
  <DataTable
    :value="documents"
    table-style="min-width: 50rem"
    selection-mode="single"
    :selection="selectedDocument"
    @update:selection="emit('selected', $event)"
  >
    <Column
      field="title"
      :header="t('document.list.title')"
    >
      <template #body="{ data }">
        <p class="font-bold">
          {{ data.document_title }}
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
          rounded
          size="small"
          variant="outlined"
          icon="pi pi-download"
          @click="() => downloadFile(data.source)"
        />
      </template>
    </Column>
  </DataTable>
</template>

<script setup lang="ts">
import { getFileUrl, type IngestedDocument } from '@core/sdk/client'

const route = useRoute()
const { t } = useI18n()

const props = defineProps<{
  documents: IngestedDocument[]
}>()

const emit = defineEmits<{
  selected: [document: IngestedDocument]
}>()

const formatted = (datestr: string) => useDateFormat(new Date(datestr), 'DD.MM.YYYY')

const selectedDocument = computed(() => {
  return props.documents.filter((document: IngestedDocument) => {
    return document.id === route.params.document_id
  })
})

const downloadFile = async (src: string) => {
  const parts = src.split('/')
  const [container, file_path] = [parts[0], parts.slice(1).join('/')]

  const { url } = await getFileUrl({
    composable: '$fetch',
    path: {
      container,
      file_path,
    },
  })
  window.open(url, '_blank')
}
</script>
