<template>
  <DataTable
    :value="allDocuments"
    table-style="min-width: 50rem"
    selection-mode="single"
    :selection="selectedDocument"
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
            :class="{ 'text-surface-500': data.isProcessing }"
          >
            {{ data.document_title }}
          </p>
          <div
            v-if="data.isProcessing"
            class="flex items-center gap-2"
          >
            <ProgressSpinner
              v-if="data.status === 'processing'"
              style="width: 16px; height: 16px"
              stroke-width="4"
            />
            <ProgressBar
              v-else-if="data.status === 'uploading'"
              :value="data.progress"
              style="width: 60px; height: 8px"
            />
            <Badge
              :value="data.status === 'uploading' ? 'Uploading' : 'Processing'"
              :severity="data.status === 'uploading' ? 'info' : 'warning'"
              size="small"
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
          v-if="!data.isProcessing"
          rounded
          size="small"
          variant="outlined"
          icon="pi pi-download"
          @click="() => downloadFile(data.source)"
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
import { getFileUrl, type IngestedDocument } from '@core/sdk/client'

const route = useRoute()
const { t } = useI18n()

const props = defineProps<{
  documents: IngestedDocument[]
  processingDocuments?: Array<{
    id: string
    document_title: string
    created_at: string
    status: 'uploading' | 'processing'
    progress?: number
  }>
}>()

const emit = defineEmits<{
  selected: [document: IngestedDocument]
}>()

const formatted = (datestr: string) => useDateFormat(new Date(datestr), 'DD.MM.YYYY')

const formatDate = (datestr: string, isProcessing: boolean) => {
  if (isProcessing) {
    return useDateFormat(new Date(datestr), 'DD.MM.YYYY HH:mm')
  }
  return formatted(datestr)
}

// Combine regular documents with processing documents
const allDocuments = computed(() => {
  const processing = (props.processingDocuments || []).map(doc => ({
    ...doc,
    isProcessing: true,
    updated_at: doc.created_at,
    number_of_pages: null,
    source: null,
  }))

  const regular = props.documents.map(doc => ({
    ...doc,
    isProcessing: false,
  }))

  // Put processing documents at the top
  return [...processing, ...regular]
})

const selectedDocument = computed(() => {
  return props.documents.filter((document: IngestedDocument) => {
    return document.id === route.params.document_id
  })
})

const handleSelection = (document: any) => {
  // Only allow selection of non-processing documents
  if (!document.isProcessing) {
    emit('selected', document as IngestedDocument)
  }
}

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
