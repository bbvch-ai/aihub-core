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
    <p
      v-else-if="failed"
      class="text-sm text-surface-500"
    >
      {{ t('userFiles.preview.failed') }}
    </p>
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
      v-else-if="kind === 'tooLarge'"
      class="text-sm text-surface-500"
    >
      {{ t('userFiles.preview.tooLarge') }}
    </p>
    <p
      v-else-if="kind === 'markdown' && !markdown.trim()"
      class="text-sm text-surface-500"
    >
      {{ t('userFiles.preview.empty') }}
    </p>
    <div
      v-else-if="kind === 'markdown'"
      class="flex flex-col gap-2"
    >
      <Message
        v-if="truncated"
        severity="secondary"
        size="small"
        variant="simple"
      >
        {{ t('userFiles.preview.truncated') }}
      </Message>
      <div class="max-h-[70vh] overflow-auto rounded border border-surface-200 bg-surface-0 p-3 dark:border-surface-700 dark:bg-surface-900">
        <MarkdownRenderer :md="toMdcMarkdown(markdown)" />
      </div>
    </div>
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
const { fetchBlob, fetchPreview, download } = useUserFileContent()

const IMAGE_EXTENSIONS = new Set(['png', 'jpg', 'jpeg', 'gif', 'webp'])
const TEXT_EXTENSIONS = new Set(['txt', 'md', 'csv', 'json', 'log', 'py', 'yaml', 'yml', 'xml', 'html', 'js', 'ts', 'sql'])
// Office documents a browser cannot show; the API converts them to markdown the way an agent reads them.
const MARKDOWN_EXTENSIONS = new Set(['docx', 'xlsx', 'xls', 'pptx'])
const MAX_TEXT_BYTES = 2 * 1024 * 1024
// Matches UserKnowledgeService.MAX_PREVIEW_BYTES, so a file the API would refuse is not sent for conversion.
const MAX_MARKDOWN_BYTES = 20 * 1024 * 1024

const objectUrl = ref<string | null>(null)
const text = ref('')
const markdown = ref('')
const truncated = ref(false)
const failed = ref(false)
const isLoading = ref(false)

const kind = computed(() => {
  const extension = props.entry.name.split('.').pop()?.toLowerCase() ?? ''
  if (IMAGE_EXTENSIONS.has(extension)) return 'image'
  if (extension === 'pdf') return 'pdf'
  if (TEXT_EXTENSIONS.has(extension) && (props.entry.size ?? 0) <= MAX_TEXT_BYTES) return 'text'
  if (MARKDOWN_EXTENSIONS.has(extension)) return (props.entry.size ?? 0) <= MAX_MARKDOWN_BYTES ? 'markdown' : 'tooLarge'
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
  markdown.value = ''
  truncated.value = false
  failed.value = false
  isLoading.value = previewKind !== 'none' && previewKind !== 'tooLarge'
  if (!isLoading.value) return
  try {
    if (previewKind === 'markdown') {
      const preview = await fetchPreview(props.entry.path)
      if (generation !== loadGeneration) return
      markdown.value = preview.markdown
      truncated.value = preview.truncated
      return
    }
    const blob = await fetchBlob(props.entry.path)
    const content = previewKind === 'text' ? await blob.text() : null
    if (generation !== loadGeneration) return
    if (content === null) objectUrl.value = URL.createObjectURL(blob)
    else text.value = content
  }
  catch {
    // The API client already logs the response; the reader is told the file can still be downloaded.
    if (generation === loadGeneration) failed.value = true
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
