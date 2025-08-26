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
import type { DocumentDTO } from '@core/sdk/client'

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

const toDocument = (document: DocumentDTO) => {
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

  // Refresh the document list to show the newly uploaded processing documents
  refetch()
}
</script>
