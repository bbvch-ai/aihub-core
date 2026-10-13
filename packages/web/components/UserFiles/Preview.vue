<template>
  <div class="flex h-full flex-col gap-3">
    <div class="flex items-center justify-between gap-2">
      <p class="truncate font-semibold">
        {{ entry.name }}
      </p>
      <div class="flex gap-1">
        <Button
          v-tooltip.bottom="t('userFiles.actions.download')"
          icon="pi pi-download"
          size="small"
          text
          @click="download(entry.path, entry.name)"
        />
        <Button
          v-tooltip.bottom="t('userFiles.actions.close')"
          icon="pi pi-times"
          size="small"
          text
          @click="emit('close')"
        />
      </div>
    </div>
    <ProgressBar
      v-if="isLoading"
      mode="indeterminate"
      style="height: 2px"
    />
    <img
      v-else-if="kind === 'image' && objectUrl"
      :src="objectUrl"
      :alt="entry.name"
      class="max-h-[70vh] self-start rounded border border-surface-200 object-contain dark:border-surface-700"
    >
    <iframe
      v-else-if="kind === 'pdf' && objectUrl"
      :src="objectUrl"
      :title="entry.name"
      class="h-[70vh] w-full rounded border border-surface-200 dark:border-surface-700"
    />
    <pre
      v-else-if="kind === 'text'"
      class="max-h-[70vh] overflow-auto whitespace-pre-wrap rounded border border-surface-200 bg-surface-0 p-3 text-xs dark:border-surface-700 dark:bg-surface-900"
    >{{ text }}</pre>
    <p
      v-else
      class="text-sm text-surface-500"
    >
      {{ t('userFiles.preview.unavailable') }}
    </p>
  </div>
</template>

<script setup lang="ts">
import type { FileEntryDto } from '@core/sdk/client'

const props = defineProps<{ entry: FileEntryDto }>()
const emit = defineEmits<{ close: [] }>()
const { t } = useI18n()
const { fetchBlob, download } = useUserFileContent()

const IMAGE_EXTENSIONS = new Set(['png', 'jpg', 'jpeg', 'gif', 'webp'])
const TEXT_EXTENSIONS = new Set(['txt', 'md', 'csv', 'json', 'log', 'py', 'yaml', 'yml', 'xml', 'html', 'js', 'ts', 'sql'])
const MAX_TEXT_BYTES = 2 * 1024 * 1024

const objectUrl = ref<string | null>(null)
const text = ref('')
const isLoading = ref(false)

const kind = computed(() => {
  const extension = props.entry.name.split('.').pop()?.toLowerCase() ?? ''
  if (IMAGE_EXTENSIONS.has(extension)) return 'image'
  if (extension === 'pdf') return 'pdf'
  if (TEXT_EXTENSIONS.has(extension) && (props.entry.size ?? 0) <= MAX_TEXT_BYTES) return 'text'
  return 'none'
})

// Only the latest load may touch the preview: one overtaken by another selection or by unmounting is dropped.
let loadGeneration = 0

const revokeObjectUrl = () => {
  if (objectUrl.value) URL.revokeObjectURL(objectUrl.value)
  objectUrl.value = null
}

const load = async () => {
  const generation = ++loadGeneration
  const previewKind = kind.value
  revokeObjectUrl()
  text.value = ''
  isLoading.value = previewKind !== 'none'
  if (previewKind === 'none') return
  try {
    const blob = await fetchBlob(props.entry.path)
    const content = previewKind === 'text' ? await blob.text() : null
    if (generation !== loadGeneration) return
    if (content === null) objectUrl.value = URL.createObjectURL(blob)
    else text.value = content
  }
  finally {
    if (generation === loadGeneration) isLoading.value = false
  }
}

watch(() => props.entry.path, load, { immediate: true })
onBeforeUnmount(() => {
  loadGeneration++
  revokeObjectUrl()
})
</script>
