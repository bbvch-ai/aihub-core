<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('knowledge.title')"
      :loading="databasesAreLoading"
    >
      <div class="flex flex-col gap-12">
        <KnowledgeDatabaseEmptyCard @add="openNewDatabaseModal" />
        <div
          v-for="database in databases"
          :key="database.name"
        >
          <div class="flex items-center gap-2 pb-2 pl-2">
            <span class="text-sm font-medium">{{ database.display_name || capitalCase(database.name) }}</span>
            <i
              v-if="database.auto_sync"
              class="pi pi-lock text-surface-400 dark:text-surface-500"
              :title="t('knowledge.auto_sync.description')"
            />
            <i
              v-else
              class="pi pi-lock-open text-surface-400 dark:text-surface-500"
              :title="t('knowledge.manual_management.description')"
            />
            <Button
              v-if="database.deletable"
              v-tooltip.top="t('knowledge.delete_database')"
              icon="pi pi-trash"
              rounded
              text
              size="small"
              severity="danger"
              @click="openDeleteDatabaseModal(database)"
            />
          </div>
          <div class="grid grid-cols-2 gap-4 2xl:grid-cols-2">
            <KnowledgeNamespaceCard
              v-for="namespace in database.namespaces"
              :key="namespace.name"
              :namespace="namespace"
              :auto-sync="database.auto_sync"
              @click="toNamespace(database.name, namespace)"
              @upload="openUploadModal(database, namespace)"
              @edit="openEditNamespaceModal(namespace)"
              @delete="openDeleteNamespaceModal(database, namespace)"
            />
            <KnowledgeNamespaceEmptyCard
              v-if="!database.auto_sync"
              @add="openNewNamespaceModal(database.name)"
            />
          </div>
        </div>
      </div>
    </StructuralColumn>
    <NuxtPage />

    <KnowledgeDocumentUploadModal
      v-model:visible="uploadModalVisible"
      :database="selectedDatabaseForUpload"
      :namespace="selectedNamespaceForUpload"
      :database-display-name="selectedDatabaseDisplayNameForUpload"
      :namespace-display-name="selectedNamespaceDisplayNameForUpload"
      @success="handleUploadSuccess"
    />

    <KnowledgeNamespaceCreateModal
      v-model="newNamespaceModalVisible"
      :databases="databases || []"
      :initial-database="selectedDatabaseForNewNamespace"
      @success="handleCreationSuccess"
    />

    <KnowledgeNamespaceEditModal
      v-model="editNamespaceModalVisible"
      :namespace="editingNamespace"
      @success="handleUpdateSuccess"
    />

    <KnowledgeDatabaseCreateModal
      v-model="newDatabaseModalVisible"
      @success="handleDatabaseCreationSuccess"
    />

    <KnowledgeDeleteConfirmModal
      v-model:visible="deleteModalVisible"
      :title="deleteTitle"
      :warning="deleteWarning"
      :expected-name="deleteExpectedName"
      :is-deleting="isDeleting"
      @confirm="handleConfirmDelete"
    />
  </StructuralScreen>
</template>

<script setup lang="ts">
import { capitalCase } from 'change-case'

import type { DatabaseDto, NamespaceDto } from '@core/sdk/client'

const router = useRouter()
const tenantPath = useTenantPath()
const { t } = useI18n()
const toast = useToast()
const { tenantId } = useTenant()

const { databases, databasesAreLoading } = useDatabases()

const { deleteDatabase, isDeleting: isDeletingDatabase } = useDeleteDatabase()
const { deleteNamespace, isDeleting: isDeletingNamespace } = useDeleteNamespace()

const uploadModalVisible = ref(false)
const selectedDatabaseForUpload = ref('')
const selectedNamespaceForUpload = ref('')
const selectedDatabaseDisplayNameForUpload = ref('')
const selectedNamespaceDisplayNameForUpload = ref('')

const newNamespaceModalVisible = ref(false)
const selectedDatabaseForNewNamespace = ref('')

const editNamespaceModalVisible = ref(false)
const editingNamespace = ref<NamespaceDto | null>(null)

const newDatabaseModalVisible = ref(false)

const toNamespace = (database_name: string, namespace: NamespaceDto) => {
  router.push(tenantPath(`/service/knowledge/${database_name}/${namespace.name}`))
}

const openUploadModal = (database: DatabaseDto, namespace: NamespaceDto) => {
  selectedDatabaseForUpload.value = database.name
  selectedNamespaceForUpload.value = namespace.name
  selectedDatabaseDisplayNameForUpload.value = database.display_name || capitalCase(database.name)
  selectedNamespaceDisplayNameForUpload.value = namespace.display_name || capitalCase(namespace.name)
  uploadModalVisible.value = true
}

const handleUploadSuccess = (data: { files: File[], namespace: string, database: string }) => {
  uploadModalVisible.value = false
  router.push(tenantPath(`/service/knowledge/${data.database}/${data.namespace}`))
}

const openNewNamespaceModal = (databaseName: string) => {
  selectedDatabaseForNewNamespace.value = databaseName
  newNamespaceModalVisible.value = true
}

const handleCreationSuccess = (data: { database: string, namespace: string }) => {
  router.push(tenantPath(`/service/knowledge/${data.database}/${data.namespace}`))
}

const openEditNamespaceModal = (namespace: NamespaceDto) => {
  editingNamespace.value = namespace
  editNamespaceModalVisible.value = true
}

const handleUpdateSuccess = () => {
  editingNamespace.value = null
}

const openNewDatabaseModal = () => {
  newDatabaseModalVisible.value = true
}

const handleDatabaseCreationSuccess = () => {
  newDatabaseModalVisible.value = false
}

type PendingDeletion
  = | { type: 'database', database: string, name: string, count: number }
    | { type: 'namespace', database: string, namespace: string, name: string, count: number }

const deleteModalVisible = ref(false)
const pendingDeletion = ref<PendingDeletion | null>(null)

const isDeleting = computed(() => isDeletingDatabase.value || isDeletingNamespace.value)

const deleteExpectedName = computed(() => pendingDeletion.value?.name ?? '')

const deleteTitle = computed(() =>
  pendingDeletion.value?.type === 'database'
    ? t('knowledge.delete.database.title')
    : t('knowledge.delete.namespace.title'),
)

const deleteWarning = computed(() => {
  const pending = pendingDeletion.value
  if (!pending) return ''
  const params = { name: pending.name, count: pending.count }
  return pending.type === 'database'
    ? t('knowledge.delete.database.warning', params)
    : t('knowledge.delete.namespace.warning', params)
})

const documentCountFor = (database: DatabaseDto) =>
  (database.namespaces ?? []).reduce((sum, namespace) => sum + (namespace.number_of_documents ?? 0), 0)

const openDeleteDatabaseModal = (database: DatabaseDto) => {
  pendingDeletion.value = {
    type: 'database',
    database: database.name,
    name: database.name,
    count: documentCountFor(database),
  }
  deleteModalVisible.value = true
}

const openDeleteNamespaceModal = (database: DatabaseDto, namespace: NamespaceDto) => {
  pendingDeletion.value = {
    type: 'namespace',
    database: database.name,
    namespace: namespace.name,
    name: namespace.name,
    count: namespace.number_of_documents ?? 0,
  }
  deleteModalVisible.value = true
}

const handleConfirmDelete = async () => {
  const pending = pendingDeletion.value
  if (!pending) return

  try {
    if (pending.type === 'database') {
      await deleteDatabase({ tenantId: tenantId.value!, database: pending.database })
    }
    else {
      await deleteNamespace({ tenantId: tenantId.value!, database: pending.database, namespace: pending.namespace })
    }
    toast.add({
      severity: 'success',
      summary: t('knowledge.delete.scheduled.summary'),
      detail: t('knowledge.delete.scheduled.detail'),
      life: 4000,
    })
    deleteModalVisible.value = false
    pendingDeletion.value = null
  }
  catch {
    toast.add({
      severity: 'error',
      summary: t('knowledge.delete.error.summary'),
      detail: t('knowledge.delete.error.detail'),
      life: 4000,
    })
  }
}
</script>
