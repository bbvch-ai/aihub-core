<template>
  <div class="flex w-full flex-col gap-4">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <Breadcrumb
        :model="crumbs"
        class="!bg-transparent !p-0"
      >
        <template #item="{ item }">
          <button
            type="button"
            class="cursor-pointer hover:underline"
            @click="openFolder(item.folder)"
          >
            {{ item.label }}
          </button>
        </template>
      </Breadcrumb>
      <div class="flex gap-2">
        <Button
          :label="t('userFiles.actions.upload')"
          icon="pi pi-upload"
          size="small"
          :loading="isUploading"
          @click="fileInput?.click()"
        />
        <Button
          :label="t('userFiles.actions.newFolder')"
          icon="pi pi-folder-plus"
          size="small"
          severity="secondary"
          @click="openNameDialog('folder')"
        />
        <Button
          v-tooltip.bottom="t('userFiles.actions.refresh')"
          icon="pi pi-refresh"
          size="small"
          severity="secondary"
          text
          @click="refresh()"
        />
        <input
          ref="fileInput"
          type="file"
          multiple
          class="hidden"
          @change="onFilesPicked"
        >
      </div>
    </div>

    <Message
      v-if="noFileSpace"
      severity="info"
      :closable="false"
    >
      {{ t('userFiles.empty.noSpace') }}
    </Message>

    <Message
      v-else-if="loadFailed"
      severity="error"
      :closable="false"
    >
      {{ t('userFiles.error.load') }}
    </Message>

    <div
      v-else
      class="flex flex-col gap-4"
      :class="{ 'xl:flex-row': !stacked }"
    >
      <div
        class="min-w-0 flex-1 rounded-lg border-2 border-dashed p-1 transition-colors"
        :class="isDragging ? 'border-primary bg-primary-50 dark:bg-primary-950' : 'border-transparent'"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="onFilesDropped"
      >
        <DataTable
          :value="entries"
          :loading="isLoading"
          data-key="path"
          size="small"
          row-hover
          :row-class="(entry: FileEntryDto) => entry.path === selected?.path ? '!bg-primary-50 dark:!bg-primary-950' : ''"
          class="cursor-pointer"
          @row-click="onRowClick($event.data)"
        >
          <template #empty>
            <p class="py-6 text-center text-sm text-surface-500">
              {{ t('userFiles.empty.folder') }}
            </p>
          </template>
          <Column :header="t('userFiles.columns.name')">
            <template #body="{ data }">
              <button
                type="button"
                class="flex max-w-full items-center gap-2 rounded text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
                :aria-label="t(data.kind === 'folder' ? 'userFiles.actions.openFolder' : 'userFiles.actions.preview', { name: data.conversation_title ?? data.name })"
                @click.stop="onRowClick(data)"
              >
                <Icon
                  :name="data.kind === 'folder' ? 'mage:folder' : 'mage:file'"
                  class="shrink-0 text-lg text-surface-500"
                  aria-hidden="true"
                />
                <span class="truncate font-medium">{{ data.conversation_title ?? data.name }}</span>
                <span
                  v-if="data.conversation_title"
                  class="truncate text-xs text-surface-400"
                >{{ t('userFiles.conversation') }}</span>
              </button>
            </template>
          </Column>
          <Column
            :header="t('userFiles.columns.size')"
            class="w-28 whitespace-nowrap text-sm text-surface-500"
          >
            <template #body="{ data }">
              {{ data.size == null ? '' : formatSize(data.size) }}
            </template>
          </Column>
          <Column
            :header="t('userFiles.columns.modified')"
            class="w-44 whitespace-nowrap text-sm text-surface-500"
          >
            <template #body="{ data }">
              {{ useDateFormat(new Date(data.modified * 1000), 'DD.MM.YYYY HH:mm').value }}
            </template>
          </Column>
          <Column class="w-40">
            <template #body="{ data }">
              <div
                class="flex justify-end"
                @click.stop
              >
                <Button
                  v-if="data.kind === 'file'"
                  v-tooltip.bottom="t('userFiles.actions.download')"
                  icon="pi pi-download"
                  size="small"
                  text
                  @click="download(data.path, data.name)"
                />
                <Button
                  v-tooltip.bottom="t('userFiles.actions.move')"
                  icon="pi pi-folder-open"
                  size="small"
                  text
                  @click="openMoveDialog(data)"
                />
                <Button
                  v-tooltip.bottom="t('userFiles.actions.rename')"
                  icon="pi pi-pencil"
                  size="small"
                  text
                  @click="openNameDialog('rename', data)"
                />
                <Button
                  v-tooltip.bottom="t('userFiles.actions.delete')"
                  icon="pi pi-trash"
                  size="small"
                  severity="danger"
                  text
                  @click="confirmDelete(data)"
                />
              </div>
            </template>
          </Column>
        </DataTable>
      </div>
      <div
        v-if="selected"
        class="w-full"
        :class="{ 'xl:w-[45%]': !stacked }"
      >
        <UserFilesPreview
          :entry="selected"
          @close="selected = null"
        />
      </div>
    </div>

    <UserFilesMoveDialog
      v-model:visible="moveDialog.visible"
      :entry="moveDialog.entry"
      :folder="folder"
      :folders="entries.filter(entry => entry.kind === 'folder')"
      :parent-label="crumbs.length > 1 ? crumbs[crumbs.length - 2].label : t('userFiles.title')"
      @submit="onMoveSubmitted"
    />
    <UserFilesNameDialog
      v-model:visible="nameDialog.visible"
      :header="nameDialog.mode === 'folder' ? t('userFiles.actions.newFolder') : t('userFiles.actions.rename')"
      :initial-name="nameDialog.entry?.name"
      @submit="onNameSubmitted"
    />
  </div>
</template>

<script setup lang="ts">
import type { FileEntryDto } from '@core/sdk/client'

const props = withDefaults(defineProps<{ initialFolder?: string, stacked?: boolean }>(), {
  initialFolder: '.',
  stacked: false,
})
const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()

const { folder, entries, folderTitle, isLoading, error, refresh } = useUserFiles()
watch(() => props.initialFolder, value => (folder.value = value), { immediate: true })
const { uploadUserFiles, isUploading } = useUploadUserFiles()
const { createUserFolder } = useCreateUserFolder()
const { moveUserFile } = useMoveUserFile()
const { deleteUserFile } = useDeleteUserFile()
const { download } = useUserFileContent()

const selected = ref<FileEntryDto | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const nameDialog = reactive<{ visible: boolean, mode: 'folder' | 'rename', entry?: FileEntryDto }>({
  visible: false,
  mode: 'folder',
})
const moveDialog = reactive<{ visible: boolean, entry?: FileEntryDto }>({ visible: false })
const titles = reactive<Record<string, string>>({})

const errorStatus = computed(() => (error.value as { statusCode?: number } | null)?.statusCode)
const noFileSpace = computed(() => errorStatus.value === 404 && folder.value === '.')
// A conversation's folder only exists once a file lands in it, so a missing folder below the top is shown empty.
const loadFailed = computed(() => error.value != null && errorStatus.value !== 404)

watch(entries, (list) => {
  for (const entry of list) if (entry.conversation_title) titles[entry.path] = entry.conversation_title
}, { immediate: true })
watch(folderTitle, (title) => {
  if (title) titles[folder.value] = title
}, { immediate: true })

const crumbs = computed(() => {
  const parts = folder.value === '.' ? [] : folder.value.split('/')
  return [
    { label: t('userFiles.title'), folder: '.' },
    ...parts.map((part, index) => {
      const path = parts.slice(0, index + 1).join('/')
      return { label: titles[path] ?? part, folder: path }
    }),
  ]
})

const join = (name: string) => (folder.value === '.' ? name : `${folder.value}/${name}`)
const parentOf = (path: string) => (path.includes('/') ? path.slice(0, path.lastIndexOf('/')) : '.')

const openFolder = (path: string) => {
  folder.value = path
  selected.value = null
}

const onRowClick = (entry: FileEntryDto) => {
  if (entry.kind === 'folder') openFolder(entry.path)
  else selected.value = entry
}

const formatSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

const notifyFailure = (summary: string, failure: unknown) => {
  const detail = (failure as { data?: { detail?: string } })?.data?.detail
  toast.add({ severity: 'error', summary, detail, life: 5000 })
}

const uploadFiles = async (files: File[]) => {
  if (files.length === 0) return
  try {
    await uploadUserFiles({ folder: folder.value, files })
    toast.add({ severity: 'success', summary: t('userFiles.toast.uploaded', { count: files.length }), life: 3000 })
  }
  catch (failure) {
    notifyFailure(t('userFiles.toast.uploadFailed'), failure)
  }
}

const onFilesPicked = async (event: Event) => {
  const input = event.target as HTMLInputElement
  await uploadFiles([...(input.files ?? [])])
  input.value = ''
}

const onFilesDropped = async (event: DragEvent) => {
  isDragging.value = false
  await uploadFiles([...(event.dataTransfer?.files ?? [])])
}

const openNameDialog = (mode: 'folder' | 'rename', entry?: FileEntryDto) => {
  Object.assign(nameDialog, { visible: true, mode, entry })
}

const onNameSubmitted = async (name: string) => {
  try {
    if (nameDialog.mode === 'folder') {
      await createUserFolder(join(name))
    }
    else if (nameDialog.entry) {
      const parent = parentOf(nameDialog.entry.path)
      await moveUserFile({ source: nameDialog.entry.path, destination: parent === '.' ? name : `${parent}/${name}` })
      if (selected.value?.path === nameDialog.entry.path) selected.value = null
    }
  }
  catch (failure) {
    notifyFailure(t('userFiles.toast.changeFailed'), failure)
  }
}

const openMoveDialog = (entry: FileEntryDto) => {
  Object.assign(moveDialog, { visible: true, entry })
}

const onMoveSubmitted = async (targetFolder: string) => {
  const entry = moveDialog.entry
  if (!entry) return
  try {
    await moveUserFile({ source: entry.path, destination: targetFolder === '.' ? entry.name : `${targetFolder}/${entry.name}` })
    if (selected.value?.path === entry.path) selected.value = null
  }
  catch (failure) {
    notifyFailure(t('userFiles.toast.changeFailed'), failure)
  }
}

const confirmDelete = (entry: FileEntryDto) => {
  confirm.require({
    header: t('userFiles.delete.header'),
    message: t(entry.kind === 'folder' ? 'userFiles.delete.folder' : 'userFiles.delete.file', { name: entry.name }),
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await deleteUserFile(entry.path)
        if (selected.value?.path === entry.path) selected.value = null
      }
      catch (failure) {
        notifyFailure(t('userFiles.toast.changeFailed'), failure)
      }
    },
  })
}
</script>
