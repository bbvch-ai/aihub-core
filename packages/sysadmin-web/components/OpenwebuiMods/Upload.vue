<template>
  <Dialog v-model:visible="visible" modal :header="t('openwebui_mods.upload')" :style="{ width: '36rem', maxWidth: '95vw' }" :closable="!busy" :close-on-escape="!busy">
    <input type="file" accept=".zip,application/zip" :disabled="busy" :aria-label="t('openwebui_mods.upload')" @change="selectFile">
    <ProgressBar v-if="busy" class="mt-4" mode="indeterminate" style="height: 2px" />
    <div v-if="preview" class="mt-4 flex flex-col gap-3">
      <h3 class="font-semibold">{{ preview.manifest.name }} {{ preview.manifest.version }}</h3>
      <p v-if="preview.manifest.description" class="text-sm">{{ preview.manifest.description }}</p>
      <Message v-if="preview.installed_version" severity="warn" :closable="false">{{ t('openwebui_mods.replace_help', { version: preview.installed_version }) }}</Message>
      <p class="text-sm text-surface-500">{{ t(preview.manifest.backend ? 'openwebui_mods.backend_notice' : 'openwebui_mods.frontend_notice') }}</p>
    </div>
    <Message v-if="failure" severity="error" :closable="false" class="mt-4">{{ failure }}</Message>
    <template #footer>
      <Button :label="t('tenant_admin.cancel')" severity="secondary" :disabled="busy" @click="visible = false" />
      <Button :label="t(preview?.installed_version ? 'openwebui_mods.replace' : 'openwebui_mods.install')" :loading="busy" :disabled="!preview || busy" @click="install" />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { inspectOpenwebuiMod, installOpenwebuiMod, type OpenWebuiModUploadPreview, type OpenWebuiModCatalogEntry } from '~/sdk/client'

const visible = defineModel<boolean>({ required: true })
const emit = defineEmits<{ installed: [OpenWebuiModCatalogEntry] }>()
const { t } = useI18n()
const errorMessage = useOpenwebuiModError()
const file = shallowRef<File>()
const preview = ref<OpenWebuiModUploadPreview>()
const busy = ref(false)
const failure = ref('')

async function selectFile(event: Event) {
  file.value = (event.target as HTMLInputElement).files?.[0]
  preview.value = undefined
  failure.value = ''
  if (!file.value) return
  busy.value = true
  try {
    preview.value = await inspectOpenwebuiMod({ composable: '$fetch', body: file.value })
  }
  catch (error) { failure.value = errorMessage(error, t('openwebui_mods.upload_error')) }
  finally { busy.value = false }
}

async function install() {
  if (!file.value || !preview.value || busy.value) return
  busy.value = true
  failure.value = ''
  try {
    const installed = await installOpenwebuiMod({ composable: '$fetch', body: file.value, query: { replace: Boolean(preview.value.installed_version) } })
    visible.value = false
    emit('installed', installed)
  }
  catch (error) { failure.value = errorMessage(error, t('openwebui_mods.upload_error')) }
  finally { busy.value = false }
}
</script>
