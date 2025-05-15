<template>
  <StructuralColumn
    title="Documents"
    close-route="/admin/knowledge"
    :loading="isLoading"
  >
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
</template>

<script setup lang="ts">
import { useDocuments } from '@core/composables/document/useDocuments'

import type { DocumentDto } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const route = useRoute()
const router = useRouter()
const localePath = useLocalePath()

const {
  documents,
  isLoading,
  pagination,
  currentPage,
  pageSize,
  setPage,
  setPageSize,
} = useDocuments()

const toDocument = (document: DocumentDto) => {
  router.push(localePath(`/admin/knowledge/${route.params.namespace}/${document.id}/overview`))
}

const onPageChange = (event) => {
  setPageSize(event.rows)
  const newPage = Math.floor(event.first / event.rows) + 1
  setPage(newPage)
}
</script>
