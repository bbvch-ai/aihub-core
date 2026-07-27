<template>
  <div
    v-if="checkedDocuments.length > 0"
    class="mb-2 flex items-center justify-between"
  >
    <p class="text-sm">
      {{ t('document.list.selected_count', { count: checkedDocuments.length }) }}
    </p>
    <Button
      size="small"
      severity="danger"
      icon="pi pi-trash"
      :label="t('document.delete.button_selected')"
      :loading="isBatchDeleting"
      @click="confirmBatchDelete"
    />
  </div>
  <DataTable
    v-model:selection="checkedDocuments"
    :value="documents"
    data-key="id"
    table-style="min-width: 50rem"
    :row-class="getRowClass"
    :sort-field="sortField ?? undefined"
    :sort-order="sortOrder"
    removable-sort
    size="small"
    :select-all="allDeletableSelected"
    @select-all-change="onSelectAllChange"
    @row-click="handleRowClick"
    @sort="handleSort"
  >
    <Column
      selection-mode="multiple"
      header-style="width: 3rem"
    />
    <Column
      field="document_title"
      :header="t('document.list.title')"
      sortable
    >
      <template #body="{ data }">
        <div class="flex items-center gap-2">
          <p class="font-bold">
            {{ data.document_title }}
          </p>
          <div
            v-if="isDocumentDeleting(data)"
            class="flex items-center gap-2"
          >
            <Tag
              :value="t('document.delete.deleting')"
              size="small"
              icon="pi pi-trash"
              severity="danger"
            />
          </div>
          <div
            v-else-if="!data.is_ingested"
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
      field="created_at"
      :header="t('document.list.created')"
      sortable
    >
      <template #body="{ data }">
        <p>{{ formatted(data.created_at) }}</p>
      </template>
    </Column>
    <Column
      field="updated_at"
      :header="t('document.list.updated_at')"
      sortable
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
        <Badge :value="data.number_of_pages ?? '-'" />
      </template>
    </Column>
    <Column
      field="source"
      :header="t('document.list.actions')"
    >
      <template #body="{ data }">
        <div class="flex items-center gap-2">
          <Button
            v-if="data.source"
            v-tooltip.top="t('document.list.download')"
            rounded
            size="small"
            variant="outlined"
            icon="pi pi-download"
            @click.stop="() => downloadFile(data.id)"
          />
          <Button
            v-if="!isDocumentDeleting(data)"
            v-tooltip.top="t('document.delete.button')"
            rounded
            size="small"
            variant="outlined"
            severity="danger"
            icon="pi pi-trash"
            :loading="isDeleting"
            @click.stop="() => confirmDelete(data)"
          />
        </div>
      </template>
    </Column>
  </DataTable>
</template>

<script setup lang="ts">
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'

import type { DocumentDto } from '@core/sdk/client'
import type { DataTableRowClickEvent, DataTableSortEvent } from 'primevue/datatable'

const route = useRoute()
const { t } = useI18n()
const { tenantId } = useTenant()
const { getDocumentSourceUrl } = useDocumentUrl()
const { deleteDocument, isDeleting } = useDeleteDocument()
const { deleteDocuments, isDeleting: isBatchDeleting } = useDeleteDocuments()
const { isScheduled, schedule, unschedule } = useScheduledDeletions(
  () => route.params.db as string,
  () => route.params.namespace as string,
)
const confirm = useConfirm()
const toast = useToast()

const props = defineProps<{
  documents: DocumentDto[]
  sortField: string | null
  sortOrder: 1 | -1
}>()

const emit = defineEmits<{
  selected: [document: DocumentDto]
  sort: [field: string | null, order: 1 | -1]
  deleted: [documentIds: string[]]
}>()

const checkedDocuments = ref<DocumentDto[]>([])

const formatted = (datestr: string) => useDateFormat(new Date(datestr), 'DD.MM.YYYY')

const isDocumentDeleting = (document: DocumentDto) => isScheduled(document.id) && document.is_ingested

// Processing documents are mid-ingestion; removing their source now would race the pipeline.
const isDocumentDeletable = (document: DocumentDto) => document.is_ingested && !isDocumentDeleting(document)

// Ids derive from the source URI, so re-uploading a just-deleted file reuses its id. When that id
// reappears as a placeholder, the scheduled entry is stale and must be cleared.
watch(
  () => props.documents,
  (documents) => {
    const reUploadedIds = (documents ?? [])
      .filter(document => !document.is_ingested && isScheduled(document.id))
      .map(document => document.id)
    if (reUploadedIds.length > 0) {
      unschedule(reUploadedIds)
    }
  },
  { immediate: true },
)

const deletableDocuments = computed(() => props.documents.filter(isDocumentDeletable))

const allDeletableSelected = computed(
  () => deletableDocuments.value.length > 0
    && deletableDocuments.value.every(document => checkedDocuments.value.some(selected => selected.id === document.id)),
)

const onSelectAllChange = ({ checked }: { checked: boolean }) => {
  const pageIds = new Set(deletableDocuments.value.map(document => document.id))
  const selectionFromOtherPages = checkedDocuments.value.filter(selected => !pageIds.has(selected.id))
  checkedDocuments.value = checked
    ? [...selectionFromOtherPages, ...deletableDocuments.value]
    : selectionFromOtherPages
}

const handleRowClick = (event: DataTableRowClickEvent) => {
  const document = event.data as DocumentDto
  if (document.is_ingested && !isDocumentDeleting(document)) {
    emit('selected', document)
  }
}

const getRowClass = (data: DocumentDto) => {
  if (!data.is_ingested || isDocumentDeleting(data)) {
    return 'opacity-50 cursor-not-allowed pointer-events-none'
  }
  return data.id === route.params.document_id ? 'bg-surface-100 dark:bg-surface-800' : ''
}

const handleSort = (event: DataTableSortEvent) => {
  const field = event.sortField as string | null
  const order = (event.sortOrder ?? 1) as 1 | -1
  emit('sort', field, order)
}

const downloadFile = async (documentId: string) => {
  const database = route.params.db as string
  const namespace = route.params.namespace as string
  const url = await getDocumentSourceUrl(tenantId.value!, database, namespace, documentId, true)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.rel = 'noopener'
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
}

const confirmDelete = (document: DocumentDto) => {
  confirm.require({
    message: t('document.delete.confirmMessage', { title: document.document_title }),
    header: t('document.delete.title'),
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: t('common.actions.cancel'),
    acceptLabel: t('document.delete.button'),
    acceptClass: 'p-button-danger',
    accept: () => handleDelete(document),
  })
}

const handleDelete = async (document: DocumentDto) => {
  try {
    await deleteDocument({
      tenantId: tenantId.value!,
      database: route.params.db as string,
      namespace: route.params.namespace as string,
      documentId: document.id,
    })
    schedule([document.id])
    checkedDocuments.value = checkedDocuments.value.filter(selected => selected.id !== document.id)
    toast.add({
      severity: 'success',
      summary: t('document.delete.success'),
      life: 3000,
    })
    emit('deleted', [document.id])
  }
  catch (error) {
    toast.add({
      severity: 'error',
      summary: t('document.delete.error'),
      detail: error instanceof Error ? error.message : String(error),
      life: 5000,
    })
  }
}

const confirmBatchDelete = () => {
  confirm.require({
    message: t('document.delete.confirmMessageBatch', { count: checkedDocuments.value.length }),
    header: t('document.delete.title'),
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: t('common.actions.cancel'),
    acceptLabel: t('document.delete.button'),
    acceptClass: 'p-button-danger',
    accept: handleBatchDelete,
  })
}

const handleBatchDelete = async () => {
  const documentIds = checkedDocuments.value.map(document => document.id)
  try {
    const response = await deleteDocuments({
      tenantId: tenantId.value!,
      database: route.params.db as string,
      namespace: route.params.namespace as string,
      documentIds,
    })
    const deletedIds = response.results.filter(result => result.status === 'scheduled').map(result => result.document_id)
    schedule(deletedIds)
    const failedCount = response.results.length - deletedIds.length
    if (failedCount > 0) {
      toast.add({
        severity: 'warn',
        summary: t('document.delete.partial', { deleted: deletedIds.length, failed: failedCount }),
        life: 5000,
      })
    }
    else {
      toast.add({
        severity: 'success',
        summary: t('document.delete.success'),
        life: 3000,
      })
    }
    checkedDocuments.value = []
    emit('deleted', deletedIds)
  }
  catch (error) {
    toast.add({
      severity: 'error',
      summary: t('document.delete.error'),
      detail: error instanceof Error ? error.message : String(error),
      life: 5000,
    })
  }
}
</script>
