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

const handleUpload = async (data: { files: File[], namespace: string, database: string }) => {
  console.log('Upload completed successfully:', data)

  // Add processing documents to show immediate feedback
  data.files.forEach((file, index) => {
    const processingDoc = {
      id: `processing-${Date.now()}-${index}`,
      document_title: file.name.replace(/\.[^/.]+$/, ''),
      created_at: new Date().toISOString(),
      status: 'processing' as const,
      progress: 100,
    }
    processingDocuments.value.push(processingDoc)
  })

  // Simulate processing time before refreshing the document list
  setTimeout(() => {
    // Remove all processing documents and refresh the list
    processingDocuments.value = []
    refetch()
  }, 3000)
}
</script>
