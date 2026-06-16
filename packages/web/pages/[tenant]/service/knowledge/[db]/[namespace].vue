<template>
  <StructuralColumn
    :title="t('knowledge.documents.title')"
    close-route="/service/knowledge"
    :loading="isLoading"
  >
    <div class="mb-4 flex items-center gap-4">
      <IconField class="flex-1">
        <InputIcon :class="isFetching ? 'pi pi-spinner pi-spin' : 'pi pi-search'" />
        <InputText
          v-model="searchInput"
          :placeholder="t('knowledge.documents.search.placeholder')"
          class="w-full"
        />
        <InputIcon
          v-if="searchInput && !isFetching"
          class="pi pi-times cursor-pointer"
          @click="searchInput = ''"
        />
      </IconField>
      <Button
        v-if="!currentDatabase?.auto_sync"
        icon="pi pi-upload"
        :label="t('knowledge.documents.upload.title')"
        @click="openUploadModal"
      />
    </div>

    <KnowledgeDocumentList
      :documents="documents"
      :sort-field="sortState.field"
      :sort-order="sortState.order"
      @selected="toDocument"
      @sort="handleSort"
      @deleted="handleDeleted"
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
import { useDebounceFn } from '@vueuse/core'
import { useChangeCase } from '@vueuse/integrations/useChangeCase'

import type { DocumentDto } from '@core/sdk/client'

const route = useRoute()
const router = useRouter()
const tenantPath = useTenantPath()
const { t } = useI18n()

const { databases } = useDatabases()

const {
  documents,
  isLoading,
  isFetching,
  pagination,
  currentPage,
  pageSize,
  searchQuery,
  sortState,
  setPage,
  setPageSize,
  setSearch,
  setSort,
  refetch,
} = useDocuments()

const uploadModalVisible = ref(false)
const searchInput = ref(searchQuery.value ?? '')

const debouncedSearch = useDebounceFn((value: string) => {
  setSearch(value)
}, 300)

// Sync local input to composable (debounced)
watch(searchInput, (newValue) => {
  debouncedSearch(newValue)
})

// Sync composable state back to local input (e.g., on navigation)
watch(searchQuery, (newValue) => {
  if (searchInput.value !== (newValue ?? '')) {
    searchInput.value = newValue ?? ''
  }
})

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
  router.push(tenantPath(`/service/knowledge/${route.params.db}/${route.params.namespace}/${document.id}/overview`))
}

const onPageChange = (event) => {
  setPageSize(event.rows)
  const newPage = Math.floor(event.first / event.rows) + 1
  setPage(newPage)
}

const handleSort = (field: string | null, order: 1 | -1) => {
  setSort(field, order)
}

const openUploadModal = () => {
  uploadModalVisible.value = true
}

const handleUpload = () => {
  refetch()
}

const handleDeleted = (documentIds: string[]) => {
  refetch()
  if (documentIds.includes(route.params.document_id as string)) {
    router.push(tenantPath(`/service/knowledge/${route.params.db}/${route.params.namespace}`))
  }
}
</script>
