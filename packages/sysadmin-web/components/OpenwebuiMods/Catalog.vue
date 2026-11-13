<template>
  <div class="flex flex-col gap-4">
    <div>
      <h3 class="text-lg font-semibold">
        {{ t(globalScope ? 'openwebui_mods.global.title' : 'openwebui_mods.title') }}
      </h3>
      <p class="mt-1 text-sm text-surface-500">
        {{ t(globalScope ? 'openwebui_mods.global.description' : 'openwebui_mods.description') }}
      </p>
    </div>
    <div class="flex flex-wrap items-center gap-3">
      <Button
        :label="t('openwebui_mods.upload')"
        icon="pi pi-upload"
        severity="secondary"
        :disabled="saving"
        @click="uploadVisible = true"
      />
      <p class="text-sm text-surface-500">
        {{ t(globalScope ? 'openwebui_mods.global.catalog_help' : 'openwebui_mods.catalog_help') }}
      </p>
    </div>
    <Message
      v-if="loadError || catalogError"
      severity="error"
      :closable="false"
    >
      {{ t('openwebui_mods.load_error') }}
    </Message>
    <ProgressBar
      v-if="loading || loadingCatalog"
      mode="indeterminate"
      style="height: 2px"
    />
    <OpenwebuiModsGlobalStatus
      v-if="globalScope && data?.globalState"
      :state="data.globalState"
      @refresh="configuration.refetch()"
    />
    <fieldset
      v-if="draft"
      :disabled="saving"
      class="flex min-w-0 flex-col gap-4"
    >
      <OpenwebuiModsCatalogEntry
        v-for="row in visibleDraft"
        :key="`${draftKey}:${row.selection.mod_id}`"
        v-model="row.selection"
        v-model:valid="row.valid"
        :global-scope="globalScope"
        :entry="entries?.find(entry => entry.manifest.id === row.selection.mod_id)"
      />
      <div class="flex flex-wrap justify-end gap-2">
        <Button
          :label="t('tenant_admin.save')"
          icon="pi pi-save"
          :loading="saving"
          :disabled="saving || !valid"
          @click="saveDraft"
        />
      </div>
    </fieldset>
    <Button
      v-else-if="loadError || catalogError"
      :label="t('openwebui_mods.retry')"
      severity="secondary"
      @click="retryLoad"
    />
    <Message
      v-if="failure"
      severity="error"
      :closable="false"
    >
      {{ failure }}
    </Message>
    <OpenwebuiModsUpload
      v-if="uploadVisible"
      v-model="uploadVisible"
      @installed="onInstalled"
    />
  </div>
</template>

<script setup lang="ts">
import { useDocumentVisibility, useIntervalFn } from '@vueuse/core'
import { cloneDeep, isEqual } from 'lodash-es'

import type { OpenWebuiModCatalogEntry, OpenWebuiModConfiguration, OpenWebuiModSelection } from '~/sdk/client'

const props = defineProps<{ tenantId: string, globalScope?: boolean }>()
const { t } = useI18n()
const toast = useToast()
const errorMessage = useOpenwebuiModError()
const { configuration, save } = useOpenwebuiModSettings(toRef(props, 'tenantId'), props.globalScope)
const { catalog } = useOpenwebuiModCatalog()
const { data, error: loadError, isPending: loading } = configuration
const { data: entries, error: catalogError, isPending: loadingCatalog } = catalog
const scope = props.globalScope ? 'global' : 'tenant'
const localePath = useLocalePath()
const visibility = useDocumentVisibility()
useIntervalFn(() => {
  if (props.globalScope && visibility.value === 'visible') configuration.refetch()
}, 2000)
const { isLoading: saving } = save
const draft = ref<{ selection: OpenWebuiModSelection, valid: boolean }[] | null>(null)
const version = ref(0)
const draftKey = ref(0)
const failure = ref('')
const uploadVisible = ref(false)
const visibleDraft = computed(() => draft.value?.filter(row => entries.value?.some(entry => entry.manifest.id === row.selection.mod_id && entry.scopes.includes(scope))))
const valid = computed(() => visibleDraft.value?.every(row => !row.selection.enabled || row.valid) ?? false)

function includeAvailableMods() {
  if (!draft.value) return
  for (const entry of entries.value?.filter(entry => entry.scopes.includes(scope)) ?? []) {
    if (draft.value.some(row => row.selection.mod_id === entry.manifest.id)) continue
    draft.value.push({ selection: { mod_id: entry.manifest.id, enabled: false, settings: cloneDeep(entry.manifest.default_settings ?? {}) }, valid: true })
  }
}

function reset(value: OpenWebuiModConfiguration) {
  version.value = value.version ?? 0
  draftKey.value += 1
  draft.value = (value.mods ?? []).map(selection => ({
    selection: cloneDeep(selection),
    valid: true,
  }))
  includeAvailableMods()
  failure.value = ''
}

watch(() => props.tenantId, () => {
  draft.value = null
  failure.value = ''
  uploadVisible.value = false
})
watch([data, entries], ([value, catalogEntries]) => {
  if (value?.tenantId !== props.tenantId || !catalogEntries) return
  if (!draft.value) reset(value.configuration)
  else includeAvailableMods()
}, { immediate: true })

async function onInstalled(entry: OpenWebuiModCatalogEntry) {
  await Promise.all([catalog.refetch(), configuration.refetch()])
  if (props.globalScope && data.value) version.value = data.value.configuration.version ?? 0
  for (const warning of entry.warnings) toast.add({ severity: 'warn', summary: warning, life: 10000 })
  toast.add({ severity: 'success', summary: t('openwebui_mods.installed', { name: entry.manifest.name }), life: 4000 })
  if (!props.globalScope && !entry.scopes.includes('tenant')) await navigateTo(localePath('/openwebui'))
}

async function retryLoad() {
  const tenantId = props.tenantId
  await Promise.all([configuration.refetch(), catalog.refetch()])
  if (tenantId === props.tenantId && data.value?.tenantId === tenantId && !loadError.value && !catalogError.value) reset(data.value.configuration)
}

async function saveDraft() {
  if (!draft.value || !valid.value || saving.value) return
  const tenantId = props.tenantId
  failure.value = ''
  try {
    const mods = draft.value.map(row => row.selection).filter(selection => selection.enabled
      || data.value?.configuration.mods?.some(saved => saved.mod_id === selection.mod_id)
      || !isEqual(selection.settings, entries.value?.find(entry => entry.manifest.id === selection.mod_id)?.manifest.default_settings ?? {}))
    const saved = await save.mutateAsync({ tenantId, configuration: { version: version.value, mods } })
    if (tenantId !== props.tenantId) return
    reset(saved)
    toast.add({ severity: 'success', summary: t('openwebui_mods.saved'), life: 4000 })
  }
  catch (error) { if (tenantId === props.tenantId) failure.value = errorMessage(error, t('openwebui_mods.save_error')) }
}
</script>
