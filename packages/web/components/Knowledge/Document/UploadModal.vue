<template>
  <Dialog
    v-model:visible="isVisible"
    modal
    :header="t('knowledge.documents.upload.title')"
    :style="{ width: '30rem' }"
    :breakpoints="{ '1199px': '75vw', '575px': '90vw' }"
  >
    <div class="flex flex-col gap-6">
      <div
        ref="dropZone"
        class="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-surface-300 p-8 transition-colors hover:border-primary-500 hover:bg-surface-50 dark:border-surface-600 dark:hover:bg-surface-800"
        :class="{
          'border-primary-500 bg-surface-50 dark:bg-surface-800': isDragOver,
          'border-red-500 bg-red-50 dark:bg-red-900/20': hasError,
        }"
        @dragover.prevent="handleDragOver"
        @dragleave.prevent="handleDragLeave"
        @drop.prevent="handleDrop"
        @click="() => fileInput?.click()"
      >
        <i
          class="pi pi-cloud-upload mb-4 text-surface-400"
          style="font-size: 3rem"
        />
        <p class="mb-2 text-sm text-surface-600 dark:text-surface-400">
          <span class="font-semibold">{{ t('knowledge.documents.upload.drag_and_drop') }}</span>
        </p>
        <div
          v-if="selectedFiles.length > 0"
          class="mt-4 w-full"
        >
          <div
            v-for="(file, index) in selectedFiles"
            :key="index"
            class="flex items-center justify-between rounded bg-surface-100 p-2 dark:bg-surface-700"
          >
            <div class="flex items-center gap-2">
              <i class="pi pi-file text-surface-400" />
              <span class="text-sm">{{ file.name }}</span>
            </div>
            <Button
              icon="pi pi-times"
              text
              rounded
              size="small"
              severity="secondary"
              @click="removeFile(index)"
            />
          </div>
        </div>
      </div>

      <div
        v-if="props.namespace && props.database"
        class="flex flex-col gap-2"
      >
        <p class="text-sm font-medium">
          {{ t('knowledge.documents.upload.target_location.label') }}
        </p>
        <div class="flex items-center gap-2 rounded-lg border border-surface-200 bg-surface-50 p-3 dark:border-surface-700 dark:bg-surface-800">
          <i
            class="pi pi-database text-surface-400"
            style="font-size: 1rem"
          />
          <span class="text-sm text-surface-600 dark:text-surface-300">{{ databaseDisplayName }}</span>
          <i
            class="pi pi-angle-right text-surface-400"
            style="font-size: 0.8rem"
          />
          <i
            class="pi pi-folder text-primary-500"
            style="font-size: 1rem"
          />
          <span class="text-sm font-medium text-surface-800 dark:text-surface-100">{{ namespaceDisplayName }}</span>
        </div>
        <small class="text-surface-500 dark:text-surface-400">
          {{ t('knowledge.documents.upload.target_location.help') }}
        </small>
      </div>

      <Message
        v-if="errorMessage"
        severity="error"
        :closable="false"
      >
        {{ errorMessage }}
      </Message>

      <div
        v-if="isUploading"
        class="flex flex-col gap-2"
      >
        <div class="flex justify-between text-sm">
          <span>{{ currentUploadFile }}</span>
          <span>{{ uploadProgress }}%</span>
        </div>
        <ProgressBar :value="uploadProgress" />
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <Button
          :label="t('knowledge.documents.upload.actions.cancel')"
          severity="secondary"
          outlined
          :disabled="isUploading"
          @click="closeModal"
        />
        <Button
          :label="t('knowledge.documents.upload.actions.upload')"
          :disabled="!canUpload"
          :loading="isUploading"
          @click="handleUpload"
        />
      </div>
    </template>

    <input
      ref="fileInput"
      type="file"
      multiple
      :accept="acceptedFileTypesString"
      class="hidden"
      @change="handleFileSelect"
    >
  </Dialog>
</template>

<script setup lang="ts">
import { capitalCase } from 'change-case'

interface Props {
  visible: boolean
  database: string
  namespace: string
  databaseDisplayName?: string
  namespaceDisplayName?: string
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
})

const { t } = useI18n()

const databaseDisplayName = computed(() => {
  return props.databaseDisplayName || capitalCase(props.database)
})

const namespaceDisplayName = computed(() => {
  return props.namespaceDisplayName || capitalCase(props.namespace)
})

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'success': [data: { files: File[], namespace: string, database: string }]
}>()

const { uploadFile } = useFileUpload()
const { supportedFileTypes } = useSupportedFileTypes()
const { tenantId } = useTenant()

const acceptedFileTypesString = computed(() => {
  return (supportedFileTypes.value ?? []).join(', ')
})
const selectedFiles = ref<File[]>([])
const isDragOver = ref(false)
const isUploading = ref(false)
const errorMessage = ref('')
const hasError = ref(false)
const uploadProgress = ref(0)
const currentUploadFile = ref('')

const fileInput = ref<HTMLInputElement>()

const isVisible = computed({
  get: () => props.visible,
  set: value => emit('update:visible', value),
})

const canUpload = computed(() => {
  return selectedFiles.value.length > 0 && !isUploading.value
})

const addFiles = (files: FileList | File[]) => {
  errorMessage.value = ''
  hasError.value = false

  const validFiles: File[] = []
  const invalidFiles: File[] = []
  const supportedTypes: string[] = supportedFileTypes.value ?? []

  for (const file of Array.from(files)) {
    const fileExtension = `.${file.name.split('.').pop()?.toLowerCase()}`

    const isDuplicate = selectedFiles.value.some(existing => existing.name === file.name && existing.size === file.size)
    const isSupported = supportedTypes.includes(fileExtension)

    if (!isDuplicate && isSupported) {
      validFiles.push(file)
    }
    else if (!isSupported) {
      invalidFiles.push(file)
    }
  }

  if (validFiles.length > 0) {
    selectedFiles.value.push(...validFiles)
  }

  if (invalidFiles.length > 0) {
    hasError.value = true
    errorMessage.value = t('knowledge.documents.upload.errors.unsupported_file_type', {
      count: invalidFiles.length,
      supportedTypes: acceptedFileTypesString.value,
    })
  }
}

const removeFile = (index: number) => {
  selectedFiles.value.splice(index, 1)
  errorMessage.value = ''
  hasError.value = false
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    addFiles(target.files)
  }
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = true
}

const handleDragLeave = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false

  if (event.dataTransfer?.files) {
    addFiles(event.dataTransfer.files)
  }
}

const handleUpload = async () => {
  if (!canUpload.value) return

  const namespace = props.namespace
  const database = props.database

  isUploading.value = true
  errorMessage.value = ''

  for (const file of selectedFiles.value) {
    currentUploadFile.value = file.name

    await uploadFile({
      filename: file.name,
      file,
      namespace,
      database,
      tenantId: tenantId.value!,
    })
  }

  emit('success', { files: selectedFiles.value, namespace, database })
  closeModal()
}

const resetState = () => {
  selectedFiles.value = []
  errorMessage.value = ''
  hasError.value = false
  isUploading.value = false
  uploadProgress.value = 0
  currentUploadFile.value = ''
}

const closeModal = () => {
  resetState()
  emit('update:visible', false)
}

watch(() => props.visible, (newVal) => {
  if (newVal) {
    resetState()
  }
})
</script>
