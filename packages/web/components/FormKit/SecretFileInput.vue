<template>
  <div class="flex flex-col gap-2">
    <input
      ref="fileInput"
      type="file"
      class="hidden"
      :accept="accept"
      @change="onFileChosen"
    >

    <button
      v-if="state === 'empty'"
      :id="context.id"
      type="button"
      class="flex w-full cursor-pointer items-center gap-3 rounded-lg border-2 border-dashed border-surface-300 p-4 text-left transition-colors hover:border-primary-500 hover:bg-surface-50 dark:border-surface-600 dark:hover:bg-surface-800"
      :class="{ 'border-primary-500 bg-surface-50 dark:bg-surface-800': isDragOver }"
      @click="chooseFile"
      @dragover.prevent="isDragOver = true"
      @dragleave.prevent="isDragOver = false"
      @drop.prevent="onFileDropped"
    >
      <i class="pi pi-upload text-surface-400" />
      <span class="flex flex-col">
        <span class="text-sm font-semibold text-surface-700 dark:text-surface-200">
          {{ context.placeholder ?? t('form.secret_file_input.drop_hint') }}
        </span>
        <span class="text-xs text-surface-500 dark:text-surface-400">
          {{ t('form.secret_file_input.limits', { accept: accept ?? '*', size: maxSizeLabel }) }}
        </span>
      </span>
    </button>

    <div
      v-else
      class="flex items-center justify-between gap-3 rounded-lg border border-surface-200 bg-surface-50 p-3 dark:border-surface-700 dark:bg-surface-800"
    >
      <div class="flex min-w-0 items-center gap-3">
        <i
          class="pi text-surface-400"
          :class="state === 'stored' ? 'pi-lock' : 'pi-file'"
        />
        <div class="flex min-w-0 flex-col">
          <span class="truncate text-sm font-medium text-surface-800 dark:text-surface-100">
            {{ state === 'stored' ? t('form.secret_file_input.stored') : (fileName ?? t('form.secret_file_input.selected')) }}
          </span>
          <span
            v-if="state === 'selected' && clientEmail"
            class="truncate text-xs text-surface-500 dark:text-surface-400"
          >
            {{ t('form.secret_file_input.client_email', { email: clientEmail }) }}
          </span>
        </div>
      </div>
      <div class="flex shrink-0 items-center gap-1">
        <Button
          :id="context.id"
          :label="t('form.secret_file_input.replace')"
          icon="pi pi-refresh"
          size="small"
          severity="secondary"
          text
          @click="chooseFile"
        />
        <Button
          v-tooltip.top="t('form.secret_file_input.remove')"
          :aria-label="t('form.secret_file_input.remove')"
          icon="pi pi-trash"
          size="small"
          severity="secondary"
          text
          rounded
          @click="removeFile"
        />
      </div>
    </div>

    <Message
      v-if="errorMessage"
      severity="error"
      size="small"
      variant="simple"
    >
      {{ errorMessage }}
    </Message>
  </div>
</template>

<script setup lang="ts">
interface SecretFileInputProps {
  context: {
    id: string
    node: { input: (value: string) => void }
    value?: string | null
    accept?: string
    maxSizeBytes?: number
    placeholder?: string
  }
}

// The API returns a stored secret as this mask followed by a handle, never the secret itself
// (SecretEncryptionService in packages/core); resubmitting it untouched keeps the stored value.
const STORED_SECRET_MASK = '••••••••'
const DEFAULT_MAX_SIZE_BYTES = 65536

const props = defineProps<SecretFileInputProps>()
const { t } = useI18n()

const fileInput = ref<HTMLInputElement>()
const isDragOver = ref(false)
const fileName = ref<string | null>(null)
const clientEmail = ref<string | null>(null)
const errorMessage = ref<string | null>(null)

const accept = computed(() => props.context.accept)
const maxSizeBytes = computed(() => props.context.maxSizeBytes ?? DEFAULT_MAX_SIZE_BYTES)
const maxSizeLabel = computed(() => `${Math.round(maxSizeBytes.value / 1024)} KB`)
const expectsJson = computed(() => accept.value?.includes('.json') ?? false)

const state = computed<'empty' | 'stored' | 'selected'>(() => {
  const value = props.context.value
  if (!value) return 'empty'
  return value.startsWith(STORED_SECRET_MASK) ? 'stored' : 'selected'
})

function chooseFile() {
  fileInput.value?.click()
}

async function onFileChosen(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  // Cleared so picking the same file again after a failed attempt still fires `change`.
  input.value = ''
  if (file) await acceptFile(file)
}

async function onFileDropped(event: DragEvent) {
  isDragOver.value = false
  const file = event.dataTransfer?.files?.[0]
  if (file) await acceptFile(file)
}

async function acceptFile(file: File) {
  errorMessage.value = null
  if (file.size > maxSizeBytes.value) {
    errorMessage.value = t('form.secret_file_input.too_large', { size: maxSizeLabel.value })
    return
  }
  const contents = await file.text()
  let parsed: unknown = null
  if (expectsJson.value) {
    try {
      parsed = JSON.parse(contents)
    }
    catch {
      errorMessage.value = t('form.secret_file_input.invalid_json')
      return
    }
  }
  fileName.value = file.name
  clientEmail.value = readClientEmail(parsed)
  props.context.node.input(contents)
}

// A Google service-account key names the account the Drive folder has to be shared with; showing it
// lets the admin confirm the right key was picked without ever rendering the private key.
function readClientEmail(parsed: unknown): string | null {
  if (!parsed || typeof parsed !== 'object') return null
  const email = (parsed as Record<string, unknown>).client_email
  return typeof email === 'string' ? email : null
}

function removeFile() {
  fileName.value = null
  clientEmail.value = null
  errorMessage.value = null
  props.context.node.input('')
}
</script>
