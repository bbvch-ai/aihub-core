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
          <div class="pb-2 pl-2 text-sm font-medium">
            {{ useChangeCase(database.name, 'capitalCase') }}
          </div>
          <div class="grid grid-cols-2 gap-4 2xl:grid-cols-2">
            <KnowledgeNamespaceCard
              v-for="namespace in database.namespaces"
              :key="namespace.name"
              :namespace="namespace"
              @click="toNamespace(database.name, namespace)"
              @upload="openUploadModal(database.name, namespace.name)"
              @edit="openEditNamespaceModal(namespace)"
            />
            <KnowledgeNamespaceEmptyCard @add="openNewNamespaceModal(database.name)" />
          </div>
        </div>
      </div>
    </StructuralColumn>
    <NuxtPage />

    <KnowledgeDocumentUploadModal
      v-model:visible="uploadModalVisible"
      :container="selectedDatabaseForUpload"
      :preselected-folder="selectedNamespaceForUpload"
      @upload="handleUpload"
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

import type { NamespaceDto } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()

const { databases, databasesAreLoading } = useDatabases()

const uploadModalVisible = ref(false)
const selectedDatabaseForUpload = ref('')
const selectedNamespaceForUpload = ref('')

const newNamespaceModalVisible = ref(false)
const selectedDatabaseForNewNamespace = ref('')

const editNamespaceModalVisible = ref(false)
const editingNamespace = ref<NamespaceDto | null>(null)

const toNamespace = (database_name: string, namespace: NamespaceDto) => {
  router.push(localePath(`/service/knowledge/${database_name}/${namespace.name}`))
}

const openUploadModal = (database_name: string, namespace_name: string) => {
  selectedDatabaseForUpload.value = database_name
  selectedNamespaceForUpload.value = namespace_name
  uploadModalVisible.value = true
}

const handleUpload = (data: { files: File[], namespace: string, database: string }) => {
  uploadModalVisible.value = false

  // Optionally navigate to the namespace after upload
  const localePath = useLocalePath()
  const router = useRouter()
  router.push(localePath(`/service/knowledge/${data.database}/${data.namespace}`))
}

const openNewNamespaceModal = (databaseName: string) => {
  selectedDatabaseForNewNamespace.value = databaseName
  newNamespaceModalVisible.value = true
}

const handleCreationSuccess = (data: { database: string, namespace: string }) => {
  setTimeout(() => {
    openUploadModal(data.database, data.namespace)
  }, 100)
}

const openEditNamespaceModal = (namespace: NamespaceDto) => {
  editingNamespace.value = namespace
  editNamespaceModalVisible.value = true
}

const handleUpdateSuccess = () => {
  editingNamespace.value = null
}
</script>
