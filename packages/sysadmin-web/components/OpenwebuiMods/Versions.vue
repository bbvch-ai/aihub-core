<template>
  <Dialog v-model:visible="visible" modal :header="t('openwebui_mods.versions')" :style="{ width: '48rem', maxWidth: '95vw' }" :closable="!publishing" :close-on-escape="!publishing">
    <p class="mb-4 text-sm text-surface-500">{{ t('openwebui_mods.versions_help') }}</p>
    <Message v-if="failure" severity="error" :closable="false" class="mb-4">{{ failure }}</Message>
    <Message v-if="hostError" severity="warn" :closable="false" class="mb-4">{{ t('openwebui_mods.host_error') }}</Message>
    <Message v-if="revisionError" severity="error" :closable="false">{{ t('openwebui_mods.load_error') }}</Message>
    <ProgressBar v-if="loadingRevisions" mode="indeterminate" style="height: 2px" />
    <div class="grid gap-4 sm:grid-cols-2">
      <div>
        <ul class="max-h-96 space-y-1 overflow-y-auto">
          <li v-for="source in revisions" :key="source.revision">
            <button type="button" class="w-full rounded-lg border p-3 text-left" :class="selected?.revision === source.revision ? 'border-primary bg-primary-50 dark:bg-surface-800' : 'border-transparent hover:bg-surface-100 dark:hover:bg-surface-800'" :disabled="publishing" :aria-pressed="selected?.revision === source.revision" @click="select(source)">
              <span class="block font-medium">{{ source.manifest.version }}</span>
              <time class="block text-sm text-surface-500" :datetime="source.uploaded_at.toISOString()">{{ useDateFormat(source.uploaded_at, 'DD.MM.YYYY HH:mm:ss') }}</time>
              <span class="text-xs text-surface-500">{{ source.revision.slice(0, 8) }}</span>
              <span v-if="source.revision === currentSource?.revision" class="ml-2 text-xs">{{ t('openwebui_mods.selected') }}</span>
            </button>
          </li>
        </ul>
        <div class="mt-3 flex justify-between gap-2">
          <Button :label="t('openwebui_mods.previous')" severity="secondary" text :disabled="offset === 0 || publishing" @click="offset -= 50" />
          <Button :label="t('openwebui_mods.next')" severity="secondary" text :disabled="revisions?.length !== 50 || publishing" @click="offset += 50" />
        </div>
      </div>
      <div v-if="selected" class="flex flex-col gap-3">
        <h3 class="font-semibold">{{ selected.manifest.name }} {{ selected.manifest.version }}</h3>
        <p v-if="selected.manifest.description" class="text-sm">{{ selected.manifest.description }}</p>
        <p class="text-sm text-surface-500">{{ selected.manifest.backend ? t('openwebui_mods.backend_notice') : t('openwebui_mods.frontend_notice') }}</p>
        <Message v-if="!eligible" severity="info" :closable="false">{{ t(globalScope ? 'openwebui_mods.global.version_ineligible' : 'openwebui_mods.global.global_only') }}</Message>
        <Message v-if="publicationError" severity="error" :closable="false">{{ t('openwebui_mods.load_error') }}</Message>
        <Button v-if="compatible" :label="t('openwebui_mods.use_version')" :disabled="publishing || !eligible" @click="choose(compatible)" />
        <Button v-else :label="t('openwebui_mods.publish')" :loading="publishing" :disabled="!host || publishing || loadingPublications || !!publicationError" @click="publishSelected" />
        <p class="text-sm text-surface-500">{{ t('openwebui_mods.publish_help') }}</p>
        <Message v-for="(warning, index) in warnings" :key="index" severity="warn" :closable="false">{{ warning }}</Message>
      </div>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import type { OpenWebuiModCompatibility, OpenWebuiModPublicationResponse, OpenWebuiModRevisionResponse } from '~/sdk/client'

const visible = defineModel<boolean>({ required: true })
const props = defineProps<{ modId: string, currentSource?: OpenWebuiModRevisionResponse, initialSource?: OpenWebuiModRevisionResponse, globalScope?: boolean }>()
const emit = defineEmits<{ select: [OpenWebuiModRevisionResponse, OpenWebuiModPublicationResponse] }>()
const { t } = useI18n()
const errorMessage = useOpenwebuiModError()
const versions = useOpenwebuiModVersions(toRef(props, 'modId'), props.initialSource ?? props.currentSource)
const { offset, selected } = versions
const { data: host, error: hostError } = versions.host
const { data: revisions, error: revisionError, isPending: loadingRevisions } = versions.revisions
const { data: publications, error: publicationError, isPending: loadingPublications } = versions.publications
const { isLoading: publishing } = versions.publish
const failure = ref('')
const warnings = ref<string[]>([])
const eligible = computed(() => {
  const manifest = selected.value?.manifest
  if (!manifest) return false
  return props.globalScope
    ? Boolean(manifest.backend && (manifest.backend_restart_required || Object.keys(manifest.backend_overrides ?? {}).length))
    : !(manifest.backend_restart_required || manifest.backend_overrides?.['open_webui.main:lifespan'])
})
const compatible = computed(() => publications.value?.find((publication: OpenWebuiModPublicationResponse) => host.value
  && publication.manifest.source_revision === selected.value?.revision
  && Object.entries(host.value.compatibility).every(([key, value]) => publication.manifest.compatibility[key as keyof OpenWebuiModCompatibility] === value)))

function select(source: OpenWebuiModRevisionResponse) {
  selected.value = source
  failure.value = ''
  warnings.value = []
}

async function publishSelected() {
  if (!selected.value) return
  failure.value = ''
  warnings.value = []
  try {
    const result = await versions.publish.mutateAsync(selected.value.revision)
    warnings.value = result.warnings
  }
  catch (error) { failure.value = errorMessage(error, t('openwebui_mods.publish_error')) }
}

function choose(publication: OpenWebuiModPublicationResponse) {
  if (!selected.value || !eligible.value) return
  emit('select', selected.value, publication)
  visible.value = false
}
</script>
