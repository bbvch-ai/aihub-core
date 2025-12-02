<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('knowledge.title')"
      :loading="databasesAreLoading"
    >
      <div class="flex flex-col gap-12">
        <div
          v-for="database in databases"
          :key="database.name"
        >
          <div class="flex items-center gap-2 pb-2 pl-2">
            <span class="text-sm font-medium">{{ database.display_name || useChangeCase(database.name, 'capitalCase') }}</span>
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
  </StructuralScreen>
</template>

<script setup lang="ts">
import { useChangeCase } from '@vueuse/integrations/useChangeCase'

import type { DatabaseDto, NamespaceDto } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()
const queryCache = useQueryCache()

const { databases, databasesAreLoading } = useDatabases()

const uploadModalVisible = ref(false)
const selectedDatabaseForUpload = ref('')
const selectedNamespaceForUpload = ref('')
const selectedDatabaseDisplayNameForUpload = ref('')
const selectedNamespaceDisplayNameForUpload = ref('')

const newNamespaceModalVisible = ref(false)
const selectedDatabaseForNewNamespace = ref('')

const editNamespaceModalVisible = ref(false)
const editingNamespace = ref<NamespaceDto | null>(null)

const toNamespace = (database_name: string, namespace: NamespaceDto) => {
  router.push(localePath(`/service/knowledge/${database_name}/${namespace.name}`))
}

const openUploadModal = (database: DatabaseDto, namespace: NamespaceDto) => {
  selectedDatabaseForUpload.value = database.name
  selectedNamespaceForUpload.value = namespace.name
  selectedDatabaseDisplayNameForUpload.value = database.display_name || useChangeCase(database.name, 'capitalCase')
  selectedNamespaceDisplayNameForUpload.value = namespace.display_name || useChangeCase(namespace.name, 'capitalCase')
  uploadModalVisible.value = true
}

const handleUploadSuccess = (data: { files: File[], namespace: string, database: string }) => {
  uploadModalVisible.value = false
  queryCache.invalidateQueries({ key: ['knowledge'] })
  router.push(localePath(`/service/knowledge/${data.database}/${data.namespace}`))
}

const openNewNamespaceModal = (databaseName: string) => {
  selectedDatabaseForNewNamespace.value = databaseName
  newNamespaceModalVisible.value = true
}

const handleCreationSuccess = (data: { database: string, namespace: string }) => {
  queryCache.invalidateQueries({ key: ['knowledge'] })
  router.push(localePath(`/service/knowledge/${data.database}/${data.namespace}`))
}

const openEditNamespaceModal = (namespace: NamespaceDto) => {
  editingNamespace.value = namespace
  editNamespaceModalVisible.value = true
}

const handleUpdateSuccess = () => {
  queryCache.invalidateQueries({ key: ['knowledge'] })
  editingNamespace.value = null
}
</script>
