<template>
  <StructuralColumn
    :title="t('knowledge.documents.title')"
    close-route="/service/knowledge"
    :loading="isLoading"
  >
    <div
      v-if="!currentDatabase?.auto_sync"
      class="mb-4 flex justify-end"
    >
      <Button
        icon="pi pi-upload"
        :label="t('knowledge.documents.upload.title')"
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
    :namespace="route.params.namespace as string"
    :database-display-name="databaseDisplayName"
    :namespace-display-name="namespaceDisplayName"
    @success="handleUpload"
  />
</template>

<script setup lang="ts">
import { useChangeCase } from '@vueuse/integrations/useChangeCase'

import type { DocumentDto } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const route = useRoute()
const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()

const { databases } = useDatabases()

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

const currentDatabase = computed(() => {
  return databases.value?.find(db => db.name === route.params.db)
})

const currentNamespace = computed(() => {
  return currentDatabase.value?.namespaces?.find(ns => ns.name === route.params.namespace)
})

const databaseDisplayName = computed(() => {
  return currentDatabase.value?.display_name || useChangeCase(route.params.db as string, 'capitalCase').value
})

const namespaceDisplayName = computed(() => {
  return currentNamespace.value?.display_name || useChangeCase(route.params.namespace as string, 'capitalCase').value
})

const toDocument = (document: DocumentDto) => {
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

const handleUpload = () => {
  refetch()
}
</script>
