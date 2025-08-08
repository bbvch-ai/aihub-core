<template>
  <StructuralColumn
    :title="t('knowledge.documents.title')"
    close-route="/service/knowledge"
    :loading="isLoading"
  >
    <div class="mb-4 flex justify-end">
      <Button
        icon="pi pi-upload"
        label="Upload Documents"
        @click="openUploadModal"
      />
    </div>

    <KnowledgeDocumentList
      :documents="documents"
      :processing-documents="processingDocuments"
      @selected="toDocument"
    />

    <div class="mt-4">
      <Paginator
        :rows="pageSize"
        :total-records="pagination.total"
        :rows-per-page-options="[10, 20, 30, 50]"
        :first="(currentPage - 1) * pageSize"
        @page="onPageChange"
      />
    </div>
  </StructuralColumn>
  <NuxtPage />

  <KnowledgeDocumentUploadModal
    v-model:visible="uploadModalVisible"
    :database="route.params.db as string"
    :preselected-namespace="route.params.namespace as string"
    @upload="handleUpload"
  />
</template>

<script setup lang="ts">
import type { IngestedDocument } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const route = useRoute()
const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()

const {
  documents,
  isLoading,
  pagination,
  currentPage,
  pageSize,
  setPage,
  setPageSize,
  refetch,
} = useDocuments()

const uploadModalVisible = ref(false)

const processingDocuments = ref<Array<{
  id: string
  document_title: string
  created_at: string
  status: 'uploading' | 'processing'
  progress?: number
}>>([])

const toDocument = (document: IngestedDocument) => {
  router.push(localePath(`/service/knowledge/${route.params.db}/${route.params.namespace}/${document.id}/overview`))
}

const onPageChange = (event) => {
  setPageSize(event.rows)
  const newPage = Math.floor(event.first / event.rows) + 1
  setPage(newPage)
}

const openUploadModal = () => {
  uploadModalVisible.value = true
}

const handleUpload = (data: { files: File[], namespace: string, database: string }) => {
  console.log('Upload requested:', data)
  uploadModalVisible.value = false

  data.files.forEach((file, index) => {
    const processingDoc = {
      id: `processing-${Date.now()}-${index}`,
      document_title: file.name.replace(/\.[^/.]+$/, ''),
      created_at: new Date().toISOString(),
      status: 'uploading' as const,
      progress: 0,
    }
    processingDocuments.value.push(processingDoc)

    simulateUploadProgress(processingDoc.id, file.name)
  })
}

const simulateUploadProgress = (docId: string, fileName: string) => {
  const doc = processingDocuments.value.find(d => d.id === docId)
  if (!doc) return

  const uploadInterval = setInterval(() => {
    if (doc.progress! < 100) {
      doc.progress = Math.min(100, doc.progress! + Math.random() * 20)
    }
    else {
      clearInterval(uploadInterval)
      doc.status = 'processing'

      const processingTime = 3000 + Math.random() * 7000
      setTimeout(() => {
        const index = processingDocuments.value.findIndex(d => d.id === docId)
        if (index > -1) {
          processingDocuments.value.splice(index, 1)
        }

        refetch()

        console.log(`Document "${fileName}" processed successfully`)
      }, processingTime)
    }
  }, 200)
}
</script>
