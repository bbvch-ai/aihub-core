<template>
  <Dialog
    v-model:visible="isVisible"
    modal
    :header="modalTitle"
    :style="{ width: '30rem' }"
    :breakpoints="{ '1199px': '75vw', '575px': '90vw' }"
  >
    <div class="flex flex-col gap-6">
      <!-- File Drop Zone -->
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
          <span class="font-semibold">Click to upload</span> or drag and drop
        </p>
        <p class="text-xs text-surface-500 dark:text-surface-400">
          PDF, DOC, TXT, MD (MAX. 10MB)
        </p>

        <!-- Selected Files -->
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
              <Badge
                :value="formatFileSize(file.size)"
                size="small"
              />
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

      <!-- Target Location -->
      <div
        v-if="props.preselectedNamespace && props.database"
        class="flex flex-col gap-2"
      >
        <label class="text-sm font-medium">Target Location</label>
        <div class="flex items-center gap-2 rounded-lg border border-surface-200 bg-surface-50 p-3 dark:border-surface-700 dark:bg-surface-800">
          <i
            class="pi pi-database text-surface-400"
            style="font-size: 1rem"
          />
          <span class="text-sm text-surface-600 dark:text-surface-300">{{ props.database }}</span>
          <i
            class="pi pi-angle-right text-surface-400"
            style="font-size: 0.8rem"
          />
          <i
            class="pi pi-folder text-primary-500"
            style="font-size: 1rem"
          />
          <span class="text-sm font-medium text-surface-800 dark:text-surface-100">{{ props.preselectedNamespace }}</span>
        </div>
        <small class="text-surface-500 dark:text-surface-400">
          Documents will be uploaded to this folder
        </small>
      </div>

      <!-- Error Message -->
      <Message
        v-if="errorMessage"
        severity="error"
        :closable="false"
      >
        {{ errorMessage }}
      </Message>

      <!-- Upload Progress -->
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
          label="Cancel"
          severity="secondary"
          outlined
          :disabled="isUploading"
          @click="closeModal"
        />
        <Button
          label="Upload"
          :disabled="!canUpload"
          :loading="isUploading"
          @click="handleUpload"
        />
      </div>
    </template>

    <!-- Hidden File Input -->
    <input
      ref="fileInput"
      type="file"
      multiple
      accept=".pdf,.doc,.docx,.txt,.md,.markdown"
      class="hidden"
      @change="handleFileSelect"
    >
  </Dialog>
</template>

<script setup lang="ts">
interface Props {
  visible: boolean
  database?: string
  preselectedNamespace?: string
  title?: string
}

interface Emits {
  (event: 'update:visible', value: boolean): void
  (event: 'upload', data: { files: File[], namespace: string, database: string }): void
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Upload Documents',
})

const emit = defineEmits<Emits>()

// Use the document upload composable
const { uploadDocument, validateFile } = useDocumentUpload()

// Reactive state
const selectedFiles = ref<File[]>([])
const isDragOver = ref(false)
const isUploading = ref(false)
const errorMessage = ref('')
const hasError = ref(false)
const uploadProgress = ref(0)
const currentUploadFile = ref('')

// Template refs
const fileInput = ref<HTMLInputElement>()

// Computed properties
const isVisible = computed({
  get: () => props.visible,
  set: value => emit('update:visible', value),
})

const modalTitle = computed(() => {
  if (props.preselectedNamespace && props.database) {
    return `Upload Documents to ${props.preselectedNamespace}`
  }
  return props.title
})

const canUpload = computed(() => {
  return selectedFiles.value.length > 0 && !isUploading.value
})

// Methods
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

const addFiles = (files: FileList | File[]) => {
  errorMessage.value = ''
  hasError.value = false

  const fileArray = Array.from(files)

  for (const file of fileArray) {
    const validation = validateFile(file)
    if (!validation.isValid) {
      errorMessage.value = validation.error!
      hasError.value = true
      return
    }

    // Avoid duplicates
    if (!selectedFiles.value.some(existing => existing.name === file.name && existing.size === file.size)) {
      selectedFiles.value.push(file)
    }
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

  const namespace = props.preselectedNamespace || ''
  const database = props.database || 'default'

  isUploading.value = true
  errorMessage.value = ''

  try {
    // Upload each file using the composable
    for (const file of selectedFiles.value) {
      currentUploadFile.value = file.name

      await uploadDocument({
        filename: file.name,
        file,
        namespace,
        database,
        onProgress: (progress) => {
          uploadProgress.value = progress
        },
      })
    }

    // Emit success event - this will trigger the parent component's handleUpload
    emit('upload', {
      files: selectedFiles.value,
      namespace,
      database,
    })

    // Close modal on success
    closeModal()
  }
  catch (error) {
    console.error('Upload failed:', error)
    errorMessage.value = error.message || 'Upload failed. Please try again.'
    hasError.value = true
  }
  finally {
    isUploading.value = false
    uploadProgress.value = 0
    currentUploadFile.value = ''
  }
}

const closeModal = () => {
  selectedFiles.value = []
  errorMessage.value = ''
  hasError.value = false
  isUploading.value = false
  uploadProgress.value = 0
  currentUploadFile.value = ''
  emit('update:visible', false)
}

// Reset form when modal opens
watch(() => props.visible, (newVal) => {
  if (newVal) {
    selectedFiles.value = []
    errorMessage.value = ''
    hasError.value = false
    isUploading.value = false
    uploadProgress.value = 0
    currentUploadFile.value = ''
  }
})
</script>
