<template>
  <div class="flex flex-col gap-4">
    <div>
      <h3 class="text-lg font-semibold">{{ t(globalScope ? 'openwebui_mods.global.title' : 'openwebui_mods.title') }}</h3>
      <p class="mt-1 text-sm text-surface-500">{{ t(globalScope ? 'openwebui_mods.global.description' : 'openwebui_mods.description') }}</p>
    </div>
    <div class="flex flex-wrap items-center gap-3">
      <Button :label="t('openwebui_mods.upload')" icon="pi pi-upload" severity="secondary" :loading="uploading" :disabled="saving || uploading" @click="fileInput?.click()" />
      <input ref="fileInput" type="file" accept=".zip,application/zip" class="hidden" @change="uploadFile">
      <p class="text-sm text-surface-500">{{ t(globalScope ? 'openwebui_mods.global.catalog_help' : 'openwebui_mods.catalog_help') }}</p>
    </div>
    <Message v-if="loadError || catalogError" severity="error" :closable="false">{{ t('openwebui_mods.load_error') }}</Message>
    <ProgressBar v-if="loading || loadingCatalog" mode="indeterminate" style="height: 2px" />
    <OpenwebuiModsGlobalStatus v-if="globalScope && data?.globalState" :state="data.globalState" @refresh="configuration.refetch()" />
    <fieldset v-if="draft" :disabled="saving" class="flex min-w-0 flex-col gap-4">
      <OpenwebuiModsCatalogEntry v-for="row in draft" :key="`${draftKey}:${row.selection.mod_id}`" v-model="row.selection" v-model:valid="row.valid" :global-scope="globalScope" :entry="entries?.find(entry => entry.manifest.id === row.selection.mod_id)" @versions="source => showVersions(row.selection.mod_id, source)" />
      <Message v-if="unpublishedGlobalMods.length" severity="warn" :closable="false">{{ t('openwebui_mods.global.select_before_save', { names: unpublishedGlobalMods.join(', ') }) }}</Message>
      <div class="flex flex-wrap justify-end gap-2">
        <Button :label="t('tenant_admin.save')" icon="pi pi-save" :loading="saving" :disabled="saving || !valid" @click="saveDraft" />
      </div>
    </fieldset>
    <Button v-else-if="loadError || catalogError" :label="t('openwebui_mods.retry')" severity="secondary" @click="retryLoad" />
    <Message v-if="failure" severity="error" :closable="false">{{ failure }}</Message>
    <OpenwebuiModsVersions v-if="versionMod && versionsVisible" :key="`${tenantId}:${versionMod}`" v-model="versionsVisible" :mod-id="versionMod" :current-source="versionSource" :initial-source="uploadedSource" :global-scope="globalScope" @select="selectVersion" />
  </div>
</template>

<script setup lang="ts">
import type { OpenWebuiModCatalogEntry, OpenWebuiModConfiguration, OpenWebuiModSelection, OpenWebuiModRevisionResponse, OpenWebuiModPublicationResponse } from '~/sdk/client'
import { useDocumentVisibility, useIntervalFn } from '@vueuse/core'
import { cloneDeep } from 'lodash-es'

const props = defineProps<{ tenantId: string, globalScope?: boolean }>()
const { t } = useI18n()
const toast = useToast()
const errorMessage = useOpenwebuiModError()
const { configuration, save } = useOpenwebuiModSettings(toRef(props, 'tenantId'), props.globalScope)
const { catalog, upload } = useOpenwebuiModCatalog()
const { data, error: loadError, isPending: loading } = configuration
const { data: catalogEntries, error: catalogError, isPending: loadingCatalog } = catalog
const entries = computed<OpenWebuiModCatalogEntry[] | undefined>(() => catalogEntries.value?.filter((entry: OpenWebuiModCatalogEntry) => !props.globalScope || !entry.builtin || (entry.manifest.backend
  && (entry.manifest.backend_restart_required || Object.keys(entry.manifest.backend_overrides ?? {}).length))))
const visibility = useDocumentVisibility()
useIntervalFn(() => { if (props.globalScope && visibility.value === 'visible') void configuration.refetch() }, 2000)
const { isLoading: saving } = save
const { isLoading: uploading } = upload
const draft = ref<{ selection: OpenWebuiModSelection, valid: boolean }[] | null>(null)
const version = ref(0)
const draftKey = ref(0)
const failure = ref('')
const fileInput = ref<HTMLInputElement>()
const versionMod = ref('')
const versionSource = ref<OpenWebuiModRevisionResponse>()
const uploadedSource = ref<OpenWebuiModRevisionResponse>()
const versionsVisible = ref(false)
const modsToSave = computed<OpenWebuiModSelection[] | null>(() => {
  if (!draft.value) return null
  const mods: OpenWebuiModSelection[] = []
  for (const row of draft.value) {
    const selection = row.selection
    if (selection.enabled && !row.valid) return null
    const settings = selection.settings ?? {}
    const entry = entries.value?.find(item => item.manifest.id === selection.mod_id)
    if (selection.publication || selection.enabled || entry?.builtin
      || JSON.stringify(settings) !== JSON.stringify(entry?.manifest.default_settings ?? {})) mods.push(selection)
  }
  return mods
})
const unpublishedGlobalMods = computed(() => props.globalScope
  ? (modsToSave.value ?? []).filter(selection => !selection.publication && !entries.value?.some(entry => entry.builtin && entry.manifest.id === selection.mod_id)).map(selection => selection.mod_id)
  : [])
const valid = computed(() => modsToSave.value !== null && !unpublishedGlobalMods.value.length
  && modsToSave.value.every(selection => !selection.enabled || selection.publication || entries.value?.some(entry => entry.builtin && entry.manifest.id === selection.mod_id)))

function includeAvailableMods() {
  if (!draft.value) return
  for (const entry of entries.value ?? []) {
    if (draft.value.some(row => row.selection.mod_id === entry.manifest.id)) continue
    draft.value.push({ selection: { mod_id: entry.manifest.id, enabled: false, publication: null, settings: cloneDeep(entry.manifest.default_settings ?? {}) }, valid: true })
  }
}

function reset(value: OpenWebuiModConfiguration) {
  version.value = value.version ?? 0
  draftKey.value += 1
  draft.value = (value.mods ?? []).map(selection => ({
    selection: { ...selection, enabled: selection.enabled ?? true, publication: entries.value?.some(entry => entry.builtin && entry.manifest.id === selection.mod_id) ? null : selection.publication },
    valid: true,
  }))
  includeAvailableMods()
  failure.value = ''
}

watch(() => props.tenantId, () => { draft.value = null; failure.value = ''; versionsVisible.value = false })
watch([data, entries], ([value, catalogEntries]) => {
  if (value?.tenantId !== props.tenantId || !catalogEntries) return
  if (!draft.value) reset(value.configuration)
  else includeAvailableMods()
}, { immediate: true })

function showVersions(modId: string, source?: OpenWebuiModRevisionResponse) {
  versionMod.value = modId
  versionSource.value = source
  uploadedSource.value = undefined
  versionsVisible.value = true
}

function selectVersion(source: OpenWebuiModRevisionResponse, publication: OpenWebuiModPublicationResponse) {
  const row = draft.value?.find(item => item.selection.mod_id === source.manifest.id)
  if (row) row.selection.publication = publication.revision
}

async function uploadFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  const tenantId = props.tenantId
  failure.value = ''
  try {
    const source = await upload.mutateAsync(file)
    await catalog.refetch()
    if (tenantId !== props.tenantId) return
    showVersions(source.manifest.id)
    uploadedSource.value = source
  }
  catch (error) { if (tenantId === props.tenantId) failure.value = errorMessage(error, t('openwebui_mods.upload_error')) }
}

async function retryLoad() {
  const tenantId = props.tenantId
  await Promise.all([configuration.refetch(), catalog.refetch()])
  if (tenantId === props.tenantId && data.value?.tenantId === tenantId && !loadError.value && !catalogError.value) reset(data.value.configuration)
}

async function saveDraft() {
  if (!modsToSave.value || !valid.value || saving.value) return
  const tenantId = props.tenantId
  failure.value = ''
  try {
    const mods = modsToSave.value
    const saved = await save.mutateAsync({ tenantId, configuration: { version: version.value, mods } })
    if (tenantId !== props.tenantId) return
    reset(saved)
    toast.add({ severity: 'success', summary: t('openwebui_mods.saved'), life: 4000 })
  }
  catch (error) { if (tenantId === props.tenantId) failure.value = errorMessage(error, t('openwebui_mods.save_error')) }
}
</script>
