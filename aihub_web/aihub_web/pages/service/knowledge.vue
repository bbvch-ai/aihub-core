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
          <div
            class="pb-2 pl-2 text-sm font-medium"
          >
            {{ useChangeCase(database.name, 'capitalCase') }}
          </div>
          <div class="grid grid-cols-2 gap-4 2xl:grid-cols-2">
            <KnowledgeNamespaceCard
              v-for="namespace in database.namespaces"
              :key="namespace.name"
              :namespace="namespace"
              @click="() => toNamespace(namespace)"
              @upload="(namespace) => openUploadModal(namespace)"
              @edit="(namespace) => openEditNamespaceModal(namespace)"
            />

            <div
              class="flex cursor-pointer flex-col gap-3 rounded-xl border-2 border-dashed border-surface-300 p-4 hover:border-primary-500 hover:bg-surface-50 dark:border-surface-600 dark:hover:bg-surface-800"
              @click="() => openNewNamespaceModal(database.name)"
            >
              <div class="flex items-center justify-center">
                <div class="flex items-center justify-center rounded-full bg-surface-100 p-3 dark:bg-surface-800">
                  <i
                    class="pi pi-folder-plus text-surface-400"
                    style="font-size: 1.5rem"
                  ></i>
                </div>
              </div>
              <div class="text-center">
                <h3 class="font-medium text-surface-600 dark:text-surface-400">
                  Add Folder
                </h3>
                <p class="text-sm text-surface-500 dark:text-surface-400">
                  Add a new folder to this database
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </StructuralColumn>
    <NuxtPage />

    <!-- Upload Modal -->
    <KnowledgeDocumentUploadModal
      v-model:visible="uploadModalVisible"
      :database="selectedDatabase"
      :preselected-namespace="selectedNamespace"
      @upload="handleUpload"
    />


    <!-- New Namespace Modal -->
    <Dialog
      v-model:visible="newNamespaceModalVisible"
      modal
      header="Create New Folder"
      :style="{ width: '35rem' }"
    >
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label class="text-sm font-medium">Select Database</label>
          <Dropdown
            v-model="selectedDatabaseForNamespace"
            :options="databaseOptions"
            option-label="name"
            option-value="name"
            placeholder="Choose database..."
            :class="{ 'p-invalid': newNamespaceError }"
          />
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-sm font-medium">Folder Name</label>
          <InputText
            v-model="newNamespaceName"
            placeholder="Enter folder name..."
            :class="{ 'p-invalid': newNamespaceError }"
          />
          <small class="text-gray-500">Technical identifier for the folder</small>
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-sm font-medium">Display Name</label>
          <InputText
            v-model="newNamespaceDisplayName"
            placeholder="Enter display name..."
          />
          <small class="text-gray-500">User-friendly name for the folder</small>
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-sm font-medium">Description (optional)</label>
          <Textarea
            v-model="newNamespaceDescription"
            placeholder="Enter description..."
            rows="3"
          />
          <small class="text-gray-500">Brief description of the folder's purpose</small>
        </div>

        <small
          v-if="newNamespaceError"
          class="text-red-500"
        >{{ newNamespaceError }}</small>
      </div>
      <template #footer>
        <div class="flex justify-end gap-2">
          <Button
            label="Cancel"
            severity="secondary"
            outlined
            @click="closeNewNamespaceModal"
          />
          <Button
            label="Create Folder"
            :disabled="!canCreateNamespace"
            @click="handleCreateNamespace"
          />
        </div>
      </template>
    </Dialog>

    <!-- Edit Namespace Modal -->
    <Dialog
      v-model:visible="editNamespaceModalVisible"
      modal
      header="Edit Folder"
      :style="{ width: '35rem' }"
    >
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
          <label class="text-sm font-medium">Folder</label>
          <InputText
            :value="editingNamespace?.name || ''"
            disabled
            class="bg-surface-100 dark:bg-surface-800"
          />
          <small class="text-gray-500">Technical name cannot be changed</small>
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-sm font-medium">Display Name</label>
          <InputText
            v-model="editNamespaceDisplayName"
            placeholder="Enter display name..."
          />
          <small class="text-gray-500">User-friendly name for the folder</small>
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-sm font-medium">Description (optional)</label>
          <Textarea
            v-model="editNamespaceDescription"
            placeholder="Enter description..."
            rows="3"
          />
          <small class="text-gray-500">Brief description of the folder's purpose</small>
        </div>

        <small
          v-if="editNamespaceError"
          class="text-red-500"
        >{{ editNamespaceError }}</small>
      </div>
      <template #footer>
        <div class="flex justify-end gap-2">
          <Button
            label="Cancel"
            severity="secondary"
            outlined
            @click="closeEditNamespaceModal"
          />
          <Button
            label="Save"
            @click="handleSaveNamespace"
          />
        </div>
      </template>
    </Dialog>
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
const { mutateAsync: createNamespace } = useCreateNamespace()
const { mutateAsync: updateNamespace } = useUpdateNamespace()

const uploadModalVisible = ref(false)
const selectedDatabase = ref('')
const selectedNamespace = ref('')

const newNamespaceModalVisible = ref(false)
const selectedDatabaseForNamespace = ref('')
const newNamespaceName = ref('')
const newNamespaceDisplayName = ref('')
const newNamespaceDescription = ref('')
const newNamespaceError = ref('')

const editNamespaceModalVisible = ref(false)
const editingNamespace = ref<NamespaceDto | null>(null)
const editNamespaceDisplayName = ref('')
const editNamespaceDescription = ref('')
const editNamespaceError = ref('')

// Computed properties
const databaseOptions = computed(() => databases.value || [])

const canCreateNamespace = computed(() => {
  return selectedDatabaseForNamespace.value.trim() && newNamespaceName.value.trim()
})

const toNamespace = (namespace: NamespaceDto) => {
  router.push(localePath(`/service/knowledge/${namespace.database}/${namespace.name}`))
}

const openUploadModal = (namespace: NamespaceDto) => {
  selectedDatabase.value = namespace.database
  selectedNamespace.value = namespace.name
  uploadModalVisible.value = true
}

const handleUpload = (data: { files: File[], namespace: string, database: string }) => {
  // TODO: Implement actual upload logic
  console.log('Upload requested:', data)
  uploadModalVisible.value = false

  // Show success message
  // TODO: Add toast notification or success feedback
}

// New Namespace handlers
const openNewNamespaceModal = (preselectedDatabase?: string) => {
  newNamespaceModalVisible.value = true
  if (preselectedDatabase) {
    selectedDatabaseForNamespace.value = preselectedDatabase
  }
}

const closeNewNamespaceModal = () => {
  newNamespaceModalVisible.value = false
  selectedDatabaseForNamespace.value = ''
  newNamespaceName.value = ''
  newNamespaceDisplayName.value = ''
  newNamespaceDescription.value = ''
  newNamespaceError.value = ''
}

const handleCreateNamespace = async () => {
  newNamespaceError.value = ''

  if (!selectedDatabaseForNamespace.value.trim()) {
    newNamespaceError.value = 'Please select a database'
    return
  }

  if (!newNamespaceName.value.trim()) {
    newNamespaceError.value = 'Folder name is required'
    return
  }

  const selectedDb = databases.value?.find(db => db.name === selectedDatabaseForNamespace.value)
  if (selectedDb?.namespaces?.some(ns => ns.name.toLowerCase() === newNamespaceName.value.toLowerCase())) {
    newNamespaceError.value = 'Folder with this name already exists in the selected database'
    return
  }

  try {
    const createRequest = {
      database_name: selectedDatabaseForNamespace.value,
      namespace_name: newNamespaceName.value,
      folder_name: newNamespaceName.value, // folder_name equals namespace_name
      display_name: newNamespaceDisplayName.value || newNamespaceName.value,
      description: newNamespaceDescription.value || null
    }

    // Create namespace via API
    const createdNamespace = await createNamespace(ref(createRequest))

    // Store data for upload flow
    const createdNamespaceName = newNamespaceName.value
    const databaseName = selectedDatabaseForNamespace.value

    closeNewNamespaceModal()

    setTimeout(() => {
      selectedDatabase.value = databaseName
      selectedNamespace.value = createdNamespaceName
      uploadModalVisible.value = true
    }, 100)


  } catch (error: any) {
    newNamespaceError.value = error.message || 'Failed to create folder'
  }
}

const openEditNamespaceModal = (namespace: NamespaceDto) => {
  editingNamespace.value = namespace
  editNamespaceDisplayName.value = namespace.display_name || namespace.name
  editNamespaceDescription.value = namespace.description || ''
  editNamespaceModalVisible.value = true
}

const closeEditNamespaceModal = () => {
  editNamespaceModalVisible.value = false
  editingNamespace.value = null
  editNamespaceDisplayName.value = ''
  editNamespaceDescription.value = ''
  editNamespaceError.value = ''
}

const handleSaveNamespace = async () => {
  editNamespaceError.value = ''

  if (!editingNamespace.value) {
    editNamespaceError.value = 'No folder selected for editing'
    return
  }

  try {
    // Prepare update data
    const updateRequest = {
      display_name: editNamespaceDisplayName.value || editingNamespace.value.name,
      description: editNamespaceDescription.value || null
    }

    // Update namespace via API (using name as ID for now - TODO: use actual ID when available)
    const namespaceId = editingNamespace.value.name
    const updatedNamespace = await updateNamespace({ id: namespaceId, payload: ref(updateRequest) })

    closeEditNamespaceModal()

    // TODO: Show success message

  } catch (error: any) {
    editNamespaceError.value = error.message || 'Failed to update folder'
  }
}
</script>
